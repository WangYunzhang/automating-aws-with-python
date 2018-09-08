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


import boto3
import click

from bucket import BucketManager


session = boto3.Session(profile_name='uswest2')
bucket_manager = BucketManager(session)


@click.group()
def cli():
    """List buckets and objects in a given bucket."""
    pass


@cli.command('list-buckets')
def list_buckets():
    """List all buckets."""
    for bucket in bucket_manager.all_buckets():
        click.echo(bucket)


@cli.command('list-bucket-objs')
@click.argument('bucket')
def list_bucket_objs(bucket):
    """List objects in a bucket."""
    for obj in bucket_manager.all_objs(bucket):
        click.echo(obj)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Create and configure S3 bucket."""
    s3_bucket = bucket_manager.init_bucket(bucket)
    bucket_manager.set_policy(s3_bucket)
    bucket_manager.configure_website(s3_bucket)

    return


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to BUCKET."""
    bucket_manager.sync(pathname, bucket)


if __name__ == '__main__':
    cli()
