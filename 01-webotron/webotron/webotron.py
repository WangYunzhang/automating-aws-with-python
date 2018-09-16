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
from certificate import CertificateManager
from cdn import DistributionManager

import util


session = None
bucket_manager = None
domain_manager = None
cert_manager = None
dist_manager = None


@click.group()
@click.option('--profile', default=None, help="Use a given profile.")
def cli(profile):
    """List buckets and objects in a given bucket."""
    global session, bucket_manager, domain_manager, cert_manager, dist_manager
    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile
    session = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(session)
    domain_manager = DomainManager(session)
    cert_manager = CertificateManager(session)
    dist_manager = DistributionManager(session)


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


@cli.command('find-cert')
@click.argument('domain')
def find_cert(domain):
    """Find a certificate for <DOMAIN>."""
    print(cert_manager.find_matching_cert(domain))


@cli.command('setup-cdn')
@click.argument('domain')
@click.argument('bucket')
def setup_cdn(domain, bucket):
    """Set up cdn for a domain porint to a bucket."""
    dist = dist_manager.find_matching_dist(domain)

    if not dist:
        cert = cert_manager.find_matching_cert(domain)
        if not cert:
            print("SSL is not optional at this time")
            return

        dist = dist_manager.create_dist(domain, cert)
        print("wainting for distribution deployment...")
        dist_manager.await_deploy(dist)

        zone = domain_manager.find_hosted_zone(domain) \
            or domain_manager.create_hosted_zone(domain)
    domain_manager.create_cf_domain_record(zone, domain, dist['DomainName'])
    print("Domain configured: https://{}".format(domain))

    return


if __name__ == '__main__':
    cli()
