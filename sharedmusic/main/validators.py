from django.core.exceptions import ValidationError


# Checks whether file hasn't exceeded max size
def validate_file_size(file):
    value = 1.5		# Max allowed file size, in MB
    size = round((file.size / 1024 / 1024), 2)	 # File size, in MB
    if size > value:
        raise ValidationError(
            f'Cannot upload image. File size exceeds 1.5 MB. Your file size is: {size} MB'
        )
