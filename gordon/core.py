# -*- coding: utf-8 -*-
import os
import re
import json
import random
import hashlib
import shutil
from collections import defaultdict

import six
import boto3
import jinja2
import troposphere
from clint.textui import colored, puts, indent
from botocore.exceptions import ClientError

# from . import exceptions
# from . import utils
# from . import actions
# from . import resources
# from . import protocols

SETTINGS_FILE = 'settings.yml'

# Lambda region list updated on Nov 28, 2017 from
# http://docs.aws.amazon.com/general/latest/gr/rande.html
AWS_LAMBDA_REGIONS = (
    'us-east-1',  # US East (N. Virginia)
    'us-east-2',  # US East (Ohio)
    'us-west-1',  # US West (N. California)
    'us-west-2',  # US West (Oregon)
    'ap-south-1',  # Asia Pacific (Mumbai)
    'ap-northeast-2',  # Asia Pacific (Seoul)
    'ap-southeast-1',  # Asia Pacific (Singapore)
    'ap-southeast-2',  # Asia Pacific (Sydney)
    'ap-northeast-1',  # Asia Pacific (Tokyo)
    'ca-central-1',  # Canada (Central)
    'eu-central-1',  # EU (Frankfurt)
    'eu-west-1',  # EU (Ireland)
    'eu-west-2',  # EU (London)
    'sa-east-1',  # South America (Sao Paulo)
)

# AVAILABLE_RESOURCES = {
#     'lambdas': resources.lambdas.Lambda,
#     'dynamodb': resources.dynamodb.Dynamodb,
#     'kinesis': resources.kinesis.Kinesis,
#     's3': resources.s3.BucketNotificationConfiguration,
#     'events': resources.events.CloudWatchEvent,
#     'vpcs': resources.vpcs.Vpc,
#     'contexts': resources.contexts.LambdasContexts,
#     'apigateway': resources.apigateway.ApiGateway
# }


class BaseResourceContainer(object):
    """Base abstraction about types which can define resources in their settings."""

    def __init__(self, *args, **kwargs):
        self._resources = defaultdict(list)
        self._load_resources()

    def _load_resources(self):
        """Load resources defined in ``self.settings`` and stores them in
        ``self._resources`` map."""
        puts = (getattr(self, 'project', None) or self).puts
        for resource_type, resource_cls in six.iteritems(AVAILABLE_RESOURCES):
            for name in self.settings.get(resource_type, {}):
                extra = {
                    'project': getattr(self, 'project', None) or self,
                    'app': self if hasattr(self, 'project') else None,
                }

                with indent(4 if hasattr(self, 'project') else 2):
                    puts(colored.green(u"✓ {}:{}".format(resource_type, name)))

                self._resources[resource_type].append(
                    resource_cls.factory(
                        name=name,
                        settings=self.settings.get(resource_type, {})[name],
                        **extra
                    )
                )

    def get_resources(self, resource_type):
        for r in sorted(self._resources[resource_type], key=lambda r: r.name):
            yield r


class App(BaseResourceContainer):
    """Container of resources of the same domain."""

    DEFAULT_SETTINS = {}

    def __init__(self, name, project, path=None, settings=None, *args, **kwargs):
        self.name = name
        self.project = project
        self.path = path or os.path.join(self.project.path, name)
        # if not os.path.exists(self.path):
        #     raise exceptions.AppNotFoundError(self.name, self.path)
        # self.settings = utils.load_settings(
        #     os.path.join(self.path, SETTINGS_FILE),
        #     default=self.DEFAULT_SETTINS,
        #     protocols=protocols.BASE_BUILD_PROTOCOLS
        # )
        self.settings.update(settings or {})
        super(App, self).__init__(*args, **kwargs)