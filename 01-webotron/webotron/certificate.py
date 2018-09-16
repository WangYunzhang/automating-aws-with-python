# -*- coding: utf-8 -*-

"""Classed for ACM certificate."""


class CertificateManager:
    """Manager an ACM certificate."""

    def __init__(self, session):
        """Initialize an ACM object."""
        self.session = session
        self.client = session.client('acm', region_name='us-east-1')

    def cert_matches(self, cert_arn, domain_name):
        """Test if a domain match the cert_arn."""
        cert_detail = self.client.describe_certificate(CertificateArn=cert_arn)
        alt_names = cert_detail['Certificate']['SubjectAlternativeNames']
        for name in alt_names:
            if name == domain_name or \
                (name[0] == '*' and domain_name.endswith(name[1:])):
                return True

        return False

    def find_matching_cert(self, domain_name):
        """Find a cert matching the domain."""
        paginator = self.client.get_paginator('list_certificates')
        for page in paginator.paginate(CertificateStatuses=['ISSUED']):
            for cert in page['CertificateSummaryList']:
                if self.cert_matches(cert['CertificateArn'], domain_name):
                    return cert

        return None
