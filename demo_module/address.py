from trytond.pool import Pool, PoolMeta
from trytond.model import fields

__all__ = ['Address', 'ContactMechanism']
__metaclass__ = PoolMeta

class Address:
    'Address extended to add job title'

    __name__ = 'party.address'

    title = fields.Char('Position')

class ContactMechanism:
    "Extended: active now proxy for address's active"

    __name__ = 'party.contact_mechanism'

    active = fields.Function(
        fields.Boolean('Active'), 'get_active', searcher='search_active'
    )

    def get_active(self, name):
        if self.address:
            return self.address.active
        else:
            return True

    @classmethod
    def search_active(cls, name, clause):
        # clause, eg, ('active', '=', True) 

        # normal proxy-field pattern
        base = [(('address.active',) + tuple(clause[1:]))]

        if not clause[2]:
            return base  # if no address, treat as active
        else:
            return [
                'OR',
                [('address', '=', None)],
                base
            ]
