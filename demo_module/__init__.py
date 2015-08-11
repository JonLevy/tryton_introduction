from trytond.pool import Pool
from address import Address, ContactMechanism

def register():
    Pool.register(
        Address,
        ContactMechanism,
        module='demo_module', type_='model')

