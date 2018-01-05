from django.db import models


class MarshmallowTestModel(models.Model):
    """
    Base model for tests
    """

    class Meta:
        app_label = 'tests'
        abstract = True


class ForeignKeyTarget(MarshmallowTestModel):
    text = models.CharField(
        max_length=100,
        verbose_name=_("Text comes here"),
        help_text=_("Text description.")
    )


class ForeignKeySource(MarshmallowTestModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, related_name='sources',
                               help_text='Target', verbose_name='Target',
                               on_delete=models.CASCADE)