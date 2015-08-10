from trytond.pool import Pool, PoolMeta
from trytond.model import fields

__all__ = ['Address']
__metaclass__ = PoolMeta

class Address:
    'Address extended to add job title'

    __name__ = 'party.address'

    title = fields.Char('Position')
