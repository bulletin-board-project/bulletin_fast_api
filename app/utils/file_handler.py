""" File operations utility class """

from typing import List, Dict, Any, Optional
import io
from fastapi import HTTPException, UploadFile, status
import pandas as pd


class FileHandler:
    """File operations utility class"""

    # Configuration
    MAX_FILE_SIZE_MB = 10  # Configurable
    ALLOWED_MIME_TYPES = {'text/csv', 'application/vnd.ms-excel', 'text/plain'}
    CHUNK_SIZE = 1000  # Rows per chunk

    @staticmethod
    async def read_file(
        file: UploadFile, required_columns: Optional[List[str]] = None, chunk_size: int = 100,
    ):
        """Read CSV file and return a list of dictionaries"""
        print('FILE NAME : ', file.filename)
        print('file type : ', file.content_type)
        # 1. File validation
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are allowed"
            )

        if file.content_type not in ['text/csv', 'application/vnd.ms-excel']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload a CSV file."
            )

        # Content-Type check
        if file.content_type not in ['text/csv', 'application/vnd.ms-excel', 'text/plain']:
            raise HTTPException(
                400, "Invalid file type. Only CSV is supported.")
        try:

            # 2. Read file content
            content = await file.read()
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size limit exceeded (10MB)"
                )

            if len(content) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty"
                )

            # 3. Read with pandas
            stream = io.BytesIO(content)
            reader = pd.read_csv(
                stream,
                encoding="utf-8-sig",
                dtype=str,
                na_filter=False,
                skip_blank_lines=True,
                chunksize=chunk_size
            )

            for df in reader:
                df = df.fillna('')
                df.columns = df.columns.str.strip()
                # 5. Check required columns
                if required_columns:
                    missing = [
                        c for c in required_columns if c not in df.columns]
                    if missing:
                        raise HTTPException(
                            400, f"Missing columns: {', '.join(missing)}"
                        )

                yield df.to_dict("records")

        except pd.errors.EmptyDataError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty or invalid",
            ) from e
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File encoding error. Use UTF-8 CSV.",
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read file: {str(e)}",
            ) from e

    @staticmethod
    def write_csv(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert data to CSV format"""
        try:
            if not data:
                # Return empty CSV with header
                df = pd.DataFrame(columns=['No Data Available'])
            else:
                df = pd.DataFrame(data)

            print(f"DEBUG: Excel columns = {df.columns.tolist()}")

            desired_columns = [
                'id', 'title', 'description', 'status',
                'create_user_id', 'updated_user_id',
                'created_at', 'updated_at', 'deleted_at'
            ]
            available_columns = [
                col for col in desired_columns if col in df.columns]
            df = df[available_columns]

            stream = io.StringIO()
            df.to_csv(
                stream,
                index=False,
                encoding='utf-8-sig',
                header=True,
            )
            csv_content = stream.getvalue()

            if len(df.columns) > 0:
                first_line = csv_content.split(
                    '\n')[0] if '\n' in csv_content else csv_content
                print(f"DEBUG write_csv: First line (headers) = {first_line}")

            return {
                "content": csv_content.encode('utf-8-sig'),
                "media_type": "text/csv; charset=utf-8-sig"
            }

        except Exception as e:
            print(f"ERROR in write_csv: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating CSV: {str(e)}"
            ) from e
