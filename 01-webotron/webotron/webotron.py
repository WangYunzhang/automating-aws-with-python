#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Webotron: Deploy a webiste with aws.

webtron automating the process of deploying a static website:
- configure aws s3 buckets
    - create them
    - setup them up for static website hosting
    - depoly local file to them
- configure DNS with AWS Route53
- configure CDN and SSL with Cloudfront
"""

from pathlib import Path
import mimetypes

import boto3
from botocore.exceptions import ClientError
import click


session = boto3.Session(profile_name='uswest2')
s3 = session.resource('s3')


@click.group()
def cli():
    """List buckets and objects in a given bucket."""
    pass


@cli.command('list-buckets')
def list_buckets():
    """List all buckets."""
    for bucket in s3.buckets.all():
        click.echo(bucket)


@cli.command('list-bucket-objs')
@click.argument('bucket')
def list_bucket_objs(bucket):
    """List objects in a bucket."""
    for obj in s3.Bucket(bucket).objects.all():
        click.echo(obj)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Create and configure S3 bucket."""
    s3_bucket = None
    try:
        s3_bucket = s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={
                'LocationConstraint': session.region_name
            }
        )
    except ClientError as error:
        if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
        else:
            raise error
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
    #ws = s3_bucket.Website()
    s3_bucket.Website.put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }
    })
    return


def upload_file(s3_bucket, path, key):
    """Upload a local file to s3 bucket with specified key."""
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    s3_bucket.upload_file(
        path,
        key,
        ExtraArgs={
            'ContentType': content_type,
            'ACL': 'public-read'
        })


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to BUCKET."""
    s3_bucket = s3.Bucket(bucket)
    root = Path(pathname).expanduser().resolve()

    def handle_directory(target):
        for p in target.iterdir():
            if p.is_dir():
                handle_directory(p)
            if p.is_file():
                upload_file(s3_bucket, str(p), str(p.relative_to(root)))
    handle_directory(root)


if __name__ == '__main__':
    cli()
