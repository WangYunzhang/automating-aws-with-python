import boto3
import click


session = boto3.Session()
s3 = session.resource('s3',region_name='us-east-1')

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

if __name__ == '__main__':
    cli()
