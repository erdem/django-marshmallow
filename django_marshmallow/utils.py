from collections import OrderedDict, namedtuple

from django.db.models import FileField

FieldInfo = namedtuple('FieldResult', [
    'relations',
    'all_fields'
])

RelationInfo = namedtuple('RelationInfo', [
    'model_field',
    'related_model',
    'to_many',
    'to_field',
    'has_through_model',
    'reverse'
])


def get_field_info(model):
    """
    Given a model class, returns a `FieldInfo` instance, which is a
    `namedtuple`, containing metadata about the various field types on the model
    including information about their relationships.
    """
    opts = model._meta.concrete_model._meta

    pk = _get_pk(opts)
    fields = _get_fields(opts)
    forward_relations = _get_forward_relationships(opts)
    reverse_relations = _get_reverse_relationships(opts)
    relationships = _merge_relationships(forward_relations, reverse_relations)
    all_fields = _merge_all_fields(pk, fields, forward_relations, reverse_relations)

    return FieldInfo(relationships, all_fields)


def _get_pk(opts):
    pk = opts.pk
    rel = pk.remote_field

    while rel and rel.parent_link:
        # If model is a child via multi-table inheritance, use parent's pk.
        pk = pk.remote_field.model._meta.pk
        rel = pk.remote_field

    return pk


def _get_fields(opts):
    fields = OrderedDict()
    for field in [field for field in opts.fields if field.serialize and not field.remote_field]:
        fields[field.name] = field

    return fields


def _get_to_field(field):
    return getattr(field, 'to_fields', None) and field.to_fields[0]


def _get_forward_relationships(opts):
    """
    Returns an `OrderedDict` of field names to `RelationInfo`.
    """
    forward_relations = OrderedDict()
    for field in [field for field in opts.fields if field.serialize and field.remote_field]:
        forward_relations[field.name] = RelationInfo(
            model_field=field,
            related_model=field.remote_field.model,
            to_many=False,
            to_field=_get_to_field(field),
            has_through_model=False,
            reverse=False
        )

    # Deal with forward many-to-many relationships.
    for field in [field for field in opts.many_to_many if field.serialize]:
        forward_relations[field.name] = RelationInfo(
            model_field=field,
            related_model=field.remote_field.model,
            to_many=True,
            # manytomany do not have to_fields
            to_field=None,
            has_through_model=(
                not field.remote_field.through._meta.auto_created
            ),
            reverse=False
        )

    return forward_relations


def _get_reverse_relationships(opts):
    """
    Returns an `OrderedDict` of field names to `RelationInfo`.
    """
    reverse_relations = OrderedDict()
    all_related_objects = [r for r in opts.related_objects if not r.field.many_to_many]
    for relation in all_related_objects:
        accessor_name = relation.get_accessor_name()
        reverse_relations[accessor_name] = RelationInfo(
            model_field=None,
            related_model=relation.related_model,
            to_many=relation.field.remote_field.multiple,
            to_field=_get_to_field(relation.field),
            has_through_model=False,
            reverse=True
        )

    # Deal with reverse many-to-many relationships.
    all_related_many_to_many_objects = [r for r in opts.related_objects if r.field.many_to_many]
    for relation in all_related_many_to_many_objects:
        accessor_name = relation.get_accessor_name()
        reverse_relations[accessor_name] = RelationInfo(
            model_field=None,
            related_model=relation.related_model,
            to_many=True,
            # manytomany do not have to_fields
            to_field=None,
            has_through_model=(
                (getattr(relation.field.remote_field, 'through', None) is not None) and
                not relation.field.remote_field.through._meta.auto_created
            ),
            reverse=True
        )

    return reverse_relations


def _merge_all_fields(pk, fields, forward_relations, reverse_relations):
    all_fields = OrderedDict()
    all_fields[pk.name] = pk
    all_fields.update(fields)
    all_fields.update(forward_relations)
    all_fields.update(reverse_relations)
    return all_fields


def _merge_relationships(forward_relations, reverse_relations):
    return OrderedDict(
        list(forward_relations.items()) +
        list(reverse_relations.items())
    )


def is_abstract_model(model):
    """
    Given a model class, returns a boolean True if it is abstract and False if it is not.
    """
    return hasattr(model, '_meta') and hasattr(model._meta, 'abstract') and model._meta.abstract


def construct_instance(schema, data, instance=None):
    """
    Construct and return a model instance from the bound ``schema``'s
    ``load_data``, but do not save the returned instance to the database.
    """

    ModelClass = schema.opts.model
    instance = ModelClass() if not instance else instance
    model_opts = instance._meta

    file_field_list = []

    for f in model_opts.fields:
        if f.name in data:
            if isinstance(f, FileField):
                file_field_list.append(f)
            else:
                f.save_form_data(instance, data[f.name])

    for file_field in file_field_list:
        file_field.save_form_data(instance, data[file_field.name])

    return instance
