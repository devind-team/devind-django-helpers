"""Module which change default Connection Class."""

import graphene


class CountableConnection(graphene.relay.Connection):
    """Override default connection class."""

    class Meta:
        """Metaclass with parameters."""

        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, node=None, name=None, **options):
        """Override default init with meta."""
        result = super().__init_subclass_with_meta__(node=node, name=name, **options)
        cls._meta.fields["total_count"] = graphene.Field(
            type=graphene.Int,
            name="totalCount",
            description="Number of items in the queryset.",
            required=True,
            resolver=cls.resolve_total_count,
        )
        return result

    def resolve_total_count(self, *_) -> int:
        """Resolve function for get totalCount values in queryset."""
        return self.iterable.count()
