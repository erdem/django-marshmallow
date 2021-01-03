from collections import OrderedDict

from django.conf import settings as django_settings
from django.utils.translation import gettext as _
from django.test.signals import setting_changed
from marshmallow import RAISE


DEFAULTS = {
    'DATE_FORMAT': None,
    'DATETIME_FORMAT': None,
    'RENDER_MODULE': None,
    'ORDERED': True,
    'INDEX_ERRORS': True,
    'LOAD_ONLY': (),
    'DUMP_ONLY': (),
    'UNKNOWN_FIELDS_ACTION': RAISE,
    'ORDER_BY': (),
    'ERROR_MESSAGE_OVERRIDES': {},
    'EXPAND_RELATED_PK_FIELDS': True,
    'SHOW_SELECT_OPTIONS': False,
    'USE_FILE_URL': True,
    'DOMAIN_FOR_FILE_URLS': None,
    'MISSING': None,
    'DEFAULT': None,
}


class DjangoMarshmallowSettings:
    SETTINGS_DOCUMENT_URL = ''

    def __init__(self, app_settings=None, defaults=None):
        if app_settings:
            if not isinstance(app_settings, (dict, tuple)):
                raise TypeError(_("Settings must be a tuple or dictionary"))
            self._app_settings = app_settings

        self.defaults = defaults or DEFAULTS

    @property
    def app_settings(self):
        if not hasattr(self, '_app_settings'):
            app_settings = getattr(django_settings, 'MARSHMALLOW_SETTINGS', {})
            if not isinstance(app_settings, (dict, tuple)):
                raise TypeError(_("Settings must be a tuple or dictionary"))

            self._app_settings = getattr(django_settings, 'MARSHMALLOW_SETTINGS', {})
        return self._app_settings

    def __getattr__(self, attr):
        if attr not in self.defaults.keys():
            raise AttributeError(
                _(f'Invalid settings key: {attr}, Check the settings documentation: {self.SETTINGS_DOCUMENT_URL}')
            )

        try:
            # Check if present attr in user settings
            val = self.app_settings[attr]

            # Merge app tuple settings with defaults
            if isinstance(val, tuple):
                try:
                    app_bundle = OrderedDict(val)
                    default_bundle = OrderedDict(self.defaults[attr])
                    default_bundle.update(app_bundle)
                    val = default_bundle
                except ValueError:
                    raise ValueError(_(
                        f'Invalid {attr} settings value. Check the settings documentation: {self.SETTINGS_DOCUMENT_URL}'
                    ))

            # Merge app dict settings with defaults
            if isinstance(val, dict):
                default_bundle = OrderedDict(self.defaults[attr])
                default_bundle.update(val)
                val = default_bundle

        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]
            if isinstance(val, tuple) and len(val) > 0:
                try:
                    val = OrderedDict(val)
                except ValueError:
                    raise ValueError(_(
                        f'Invalid {attr} settings value. Check the settings documentation: {self.SETTINGS_DOCUMENT_URL}'
                    ))

        setattr(self, attr, val)
        return val


ma_settings = DjangoMarshmallowSettings(None, DEFAULTS)


def reload_ma_settings(*args, **kwargs):
    global ma_settings
    setting, value = kwargs['setting'], kwargs['value']
    if setting == 'MARSHMALLOW_SETTINGS' and value:
        ma_settings = DjangoMarshmallowSettings(value, DEFAULTS)


setting_changed.connect(reload_ma_settings)
