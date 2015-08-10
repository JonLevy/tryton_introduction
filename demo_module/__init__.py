from trytond.pool import Pool
from address import Address

def register():
    Pool.register(
        Address,
        module='demo_module', type_='model')

