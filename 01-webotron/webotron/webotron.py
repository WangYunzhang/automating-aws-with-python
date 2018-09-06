import boto3
import click
from botocore.exceptions import ClientError

session = boto3.Session(profile_name='uswest2')
s3 = session.resource('s3')

@click.group()
def cli():
    "list buckets and objects in a given bucket"
    pass

@cli.command('list-buckets')
def list_buckets():
    "list all buckets"
    for bucket in s3.buckets.all():
        click.echo(bucket)

@cli.command('list-bucket-objs')
@click.argument('bucket')
def list_bucket_objs(bucket):
    "list objects in a bucket"
    for obj in s3.Bucket(bucket).objects.all():
        click.echo(obj)
@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    "Create and configure S3 bucket"
    s3_bucket = None
    try:
        s3_bucket = s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={'LocationConstraint': session.region_name}
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
        else:
            raise e
    policy = """
    {
      "Version":"2012-10-17",
      "Statement":[{
      "Sid":"PublicReadGetObject",
      "Effect":"Allow",
      "Principal": "*",
          "Action":["s3:GetObject"],
          "Resource":["arn:aws:s3:::%s/*"
          ]
        }
      ]
    }
    """ % s3_bucket.name
    policy = policy.strip()
    pol = s3_bucket.Policy()
    pol.put(Policy=policy)
    ws = s3_bucket.Website()
    ws.put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }
    })
    return
if __name__ == '__main__':
    cli()
