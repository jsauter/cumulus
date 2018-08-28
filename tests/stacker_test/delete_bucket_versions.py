import boto3
import sys

bucket_name = str(sys.argv[1])

print("deleting bucket %s " % bucket_name)

session = boto3.Session()
s3 = session.resource(service_name='s3')
bucket = s3.Bucket(bucket_name)
bucket.object_versions.delete()
