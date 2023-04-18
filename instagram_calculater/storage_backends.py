from storages.backends.s3boto3 import S3Boto3Storage

class ScalewayS3Boto3Storage(S3Boto3Storage):
    location = 'ig-media'
    custom_domain = 'ig-media.s3.fr-par.scw.cloud'