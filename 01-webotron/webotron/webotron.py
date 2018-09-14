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
from domain import DomainManager

from webotron import util


session = None
bucket_manager = None
domain_manager = None


@click.group()
@click.option('--profile', default=None, help="Use a given profile.")
def cli(profile):
    """List buckets and objects in a given bucket."""
    global session, bucket_manager, domain_manager
    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile
    session = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(session)
    domain_manager = DomainManager(session)


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
    print(bucket_manager.get_bucket_url(bucket))


@cli.command('setup-domain')
@click.argument('domain')
def setup_domain(domain):
    """Configure a DOMAIN to point to a bucket."""
    bucket = domain
    zone = domain_manager.find_hosted_zone(domain) \
        or domain_manager.create_hosted_zone(domain)

    endpoint = util.get_endpoint(bucket_manager.get_bucket_location(bucket))
    domain_manager.create_s3_domain_record(zone, domain, endpoint)
    print("Domain configured: http://{}".format(domain))


if __name__ == '__main__':
    cli()
