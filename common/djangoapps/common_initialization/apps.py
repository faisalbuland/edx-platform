"""
Common initialization app for the LMS and CMS
"""

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error, Tags, register


class CommonInitializationConfig(AppConfig):
    name = 'common_initialization'
    verbose_name = 'Common Initialization'


@register(Tags.compatibility)
def validate_settings(app_configs, **kwargs):
    """
    Common settings validations for the LMS and CMS.

    Only populate this method with general settings validations which do not
    fit in the validations in other, more specific djangoapps.  Usually,
    settings which are widely used across the entire LMS or CMS can be
    validated here.
    """
    errors = []
    errors.extend(_validate_lms_root_url_setting())
    errors.extend(_validate_marketing_site_setting())
    return errors


def _validate_lms_root_url_setting():
    """
    Validates the LMS_ROOT_URL setting.
    """
    errors = []
    if not getattr(settings, 'LMS_ROOT_URL', None):
        errors.append(
            Error(
                'LMS_ROOT_URL is not defined.',
                id='common.djangoapps.common_initialization.E001',
            )
        )
    return errors


def _validate_marketing_site_setting():
    """
    Validates marketing site related settings.
    """
    errors = []
    if settings.FEATURES.get('ENABLE_MKTG_SITE'):
        if not hasattr(settings, 'MKTG_URLS'):
            errors.append(
                Error(
                    'ENABLE_MKTG_SITE is True, but MKTG_URLS is not defined.',
                    id='common.djangoapps.common_initialization.E002',
                )
            )
        if not settings.MKTG_URLS.get('ROOT'):
            errors.append(
                Error(
                    'There is no ROOT defined in MKTG_URLS.',
                    id='common.djangoapps.common_initialization.E003',
                )
            )
    return errors
