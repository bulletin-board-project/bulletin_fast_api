""" Helper """

import asyncio
from datetime import datetime
from urllib.parse import urlparse
import cloudinary
from cloudinary import uploader
import cloudinary.exceptions
from cloudinary.exceptions import Error as CloudinaryError
from fastapi import HTTPException, UploadFile, status


def upload_image(profile_image: UploadFile) -> str:
    """ Upload Image to Cloudinary """
    try:
        # Just use cloudinary.uploader directly
        upload_result = uploader.upload(
            profile_image.file,
            folder="user_profiles",
            public_id=f"profile_{datetime.now().timestamp()}",
            overwrite=True,
            resource_type="image",
            transformation=[
                {"width": 500, "height": 500, "crop": "fill"},
                {"quality": "auto:good"}
            ]
        )
        return upload_result.get("secure_url")

    except cloudinary.exceptions.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cloudinary upload failed: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        ) from e


async def upload_profile_image(profile_image: UploadFile) -> str:
    """Upload profile image to Cloudinary"""

    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
    if profile_image.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    try:
        # Method 2: Use chunks to check size (more memory efficient)
        chunk_size = 1024 * 1024  # 1MB chunks
        max_size = 5 * 1024 * 1024  # 5MB
        total_size = 0

        # Read in chunks to check size
        while True:
            chunk = await profile_image.read(chunk_size)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size must be less than 5MB"
                )

        # Reset file pointer
        await profile_image.seek(0)

        # ✅ Cloudinary is already configured in main.py
        upload_result = cloudinary.uploader.upload(
            profile_image.file,
            folder="user_profiles",
            public_id=f"profile_{int(datetime.now().timestamp())}",
            overwrite=True,
            resource_type="image",
            transformation=[
                {"width": 500, "height": 500, "crop": "fill"},
                {"quality": "auto:good"}
            ]
        )

        return upload_result.get("secure_url")

    except HTTPException:
        raise  # Re-raise HTTPException
    except cloudinary.exceptions.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cloudinary upload failed: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        ) from e


def extract_public_id_from_url(image_url: str) -> str:
    """
    Extract public_id from Cloudinary URL

    Example URL: https://res.cloudinary.com/demo/image/upload/v1234567/folder/filename.jpg
    Returns: folder/filename
    """
    try:
        parsed_url = urlparse(image_url)
        path_parts = parsed_url.path.split('/')

        # Find 'upload' in the path
        upload_index = path_parts.index(
            'upload') if 'upload' in path_parts else -1

        if upload_index >= 0 and upload_index + 1 < len(path_parts):
            # Get all parts after 'upload' (excluding version if present)
            public_id_parts = path_parts[upload_index + 1:]

            # Remove version if it's in format 'v1234567'
            if public_id_parts and public_id_parts[0].startswith('v'):
                public_id_parts = public_id_parts[1:]

            # Join parts and remove file extension
            public_id = '/'.join(public_id_parts)

            # Remove file extension (.jpg, .png, etc.)
            if '.' in public_id:
                public_id = public_id.rsplit('.', 1)[0]

            return public_id
        else:
            raise ValueError("Invalid Cloudinary URL format")

    except Exception as e:
        raise ValueError(
            f"Failed to extract public_id from URL: {str(e)}") from e


async def delete_profile_image(image_url: str) -> bool:
    """
    Delete profile image from Cloudinary

    Args:
        image_url: The Cloudinary URL of the image to delete

    Returns:
        bool: True if deletion was successful

    Raises:
        HTTPException: If deletion fails
    """
    if not image_url:
        return True  # No image to delete

    try:
        # Extract public_id from the Cloudinary URL
        public_id = extract_public_id_from_url(image_url)

        print(f"🗑️ Attempting to delete image with public_id: {public_id}")

        # Delete the image from Cloudinary
        # Using run_in_executor for async compatibility since cloudinary is blocking
        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            None,
            lambda: cloudinary.uploader.destroy(
                public_id,
                resource_type="image",
                invalidate=True  # Invalidate CDN cache
            )
        )

        # Check if deletion was successful
        if result.get("result") == "ok":
            print(f"✅ Successfully deleted image: {public_id}")
            return True
        else:
            print(f"⚠️ Cloudinary returned non-ok result: {result}")
            # Don't raise exception here - might be already deleted
            return False

    except ValueError as e:
        # If we can't parse the URL, log but don't fail
        print(f"⚠️ Could not parse Cloudinary URL: {str(e)}")
        return False

    except CloudinaryError as e:
        # Check if it's a "not found" error
        error_message = str(e).lower()
        if "not found" in error_message or "invalid" in error_message:
            print(
                f"⚠️ Image not found on Cloudinary (might be already deleted): {str(e)}")
            return False

        # For other Cloudinary errors, raise HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image from Cloudinary: {str(e)}"
        ) from e

    except Exception as e:
        # For unexpected errors, raise HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while deleting image: {str(e)}"
        ) from e
