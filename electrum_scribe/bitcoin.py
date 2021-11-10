# -*- coding: utf-8 -*-
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2011 thomasv@gitorious
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import hashlib
import ecdsa
import base64
from typing import List, Tuple, TYPE_CHECKING, Optional, Union
from enum import IntEnum

from .util import bfh, bh2u, BitcoinException, assert_bytes, to_bytes, inv_dict
from . import version
from . import segwit_addr
from . import constants
from . import ecc
from .crypto import sha256d, sha256, hash_160, hmac_oneshot, lyra2re2

if TYPE_CHECKING:
    from .network import Network


################################## transactions

COINBASE_MATURITY = 100
COIN = 100000000
TOTAL_COIN_SUPPLY_LIMIT_IN_BTC = 105120000

# supported types of transaction outputs
TYPE_ADDRESS = 0
TYPE_PUBKEY  = 1
TYPE_SCRIPT  = 2


class opcodes(IntEnum):
    # push value
    OP_0 = 0x00
    OP_FALSE = OP_0
    OP_PUSHDATA1 = 0x4c
    OP_PUSHDATA2 = 0x4d
    OP_PUSHDATA4 = 0x4e
    OP_1NEGATE = 0x4f
    OP_RESERVED = 0x50
    OP_1 = 0x51
    OP_TRUE = OP_1
    OP_2 = 0x52
    OP_3 = 0x53
    OP_4 = 0x54
    OP_5 = 0x55
    OP_6 = 0x56
    OP_7 = 0x57
    OP_8 = 0x58
    OP_9 = 0x59
    OP_10 = 0x5a
    OP_11 = 0x5b
    OP_12 = 0x5c
    OP_13 = 0x5d
    OP_14 = 0x5e
    OP_15 = 0x5f
    OP_16 = 0x60

    # control
    OP_NOP = 0x61
    OP_VER = 0x62
    OP_IF = 0x63
    OP_NOTIF = 0x64
    OP_VERIF = 0x65
    OP_VERNOTIF = 0x66
    OP_ELSE = 0x67
    OP_ENDIF = 0x68
    OP_VERIFY = 0x69
    OP_RETURN = 0x6a

    # stack ops
    OP_TOALTSTACK = 0x6b
    OP_FROMALTSTACK = 0x6c
    OP_2DROP = 0x6d
    OP_2DUP = 0x6e
    OP_3DUP = 0x6f
    OP_2OVER = 0x70
    OP_2ROT = 0x71
    OP_2SWAP = 0x72
    OP_IFDUP = 0x73
    OP_DEPTH = 0x74
    OP_DROP = 0x75
    OP_DUP = 0x76
    OP_NIP = 0x77
    OP_OVER = 0x78
    OP_PICK = 0x79
    OP_ROLL = 0x7a
    OP_ROT = 0x7b
    OP_SWAP = 0x7c
    OP_TUCK = 0x7d

    # splice ops
    OP_CAT = 0x7e
    OP_SUBSTR = 0x7f
    OP_LEFT = 0x80
    OP_RIGHT = 0x81
    OP_SIZE = 0x82

    # bit logic
    OP_INVERT = 0x83
    OP_AND = 0x84
    OP_OR = 0x85
    OP_XOR = 0x86
    OP_EQUAL = 0x87
    OP_EQUALVERIFY = 0x88
    OP_RESERVED1 = 0x89
    OP_RESERVED2 = 0x8a

    # numeric
    OP_1ADD = 0x8b
    OP_1SUB = 0x8c
    OP_2MUL = 0x8d
    OP_2DIV = 0x8e
    OP_NEGATE = 0x8f
    OP_ABS = 0x90
    OP_NOT = 0x91
    OP_0NOTEQUAL = 0x92

    OP_ADD = 0x93
    OP_SUB = 0x94
    OP_MUL = 0x95
    OP_DIV = 0x96
    OP_MOD = 0x97
    OP_LSHIFT = 0x98
    OP_RSHIFT = 0x99

    OP_BOOLAND = 0x9a
    OP_BOOLOR = 0x9b
    OP_NUMEQUAL = 0x9c
    OP_NUMEQUALVERIFY = 0x9d
    OP_NUMNOTEQUAL = 0x9e
    OP_LESSTHAN = 0x9f
    OP_GREATERTHAN = 0xa0
    OP_LESSTHANOREQUAL = 0xa1
    OP_GREATERTHANOREQUAL = 0xa2
    OP_MIN = 0xa3
    OP_MAX = 0xa4

    OP_WITHIN = 0xa5

    # crypto
    OP_RIPEMD160 = 0xa6
    OP_SHA1 = 0xa7
    OP_SHA256 = 0xa8
    OP_HASH160 = 0xa9
    OP_HASH256 = 0xaa
    OP_CODESEPARATOR = 0xab
    OP_CHECKSIG = 0xac
    OP_CHECKSIGVERIFY = 0xad
    OP_CHECKMULTISIG = 0xae
    OP_CHECKMULTISIGVERIFY = 0xaf

    # expansion
    OP_NOP1 = 0xb0
    OP_CHECKLOCKTIMEVERIFY = 0xb1
    OP_NOP2 = OP_CHECKLOCKTIMEVERIFY
    OP_CHECKSEQUENCEVERIFY = 0xb2
    OP_NOP3 = OP_CHECKSEQUENCEVERIFY
    OP_NOP4 = 0xb3
    OP_NOP5 = 0xb4
    OP_NOP6 = 0xb5
    OP_NOP7 = 0xb6
    OP_NOP8 = 0xb7
    OP_NOP9 = 0xb8
    OP_NOP10 = 0xb9

    OP_INVALIDOPCODE = 0xff

    def hex(self) -> str:
        return bytes([self]).hex()


def sha256(x):
    x = to_bytes(x, 'utf8')
    return bytes(hashlib.sha256(x).digest())
  
def msg_magic(message):
    length = bfh(var_int(len(message)))
    final = b"\x1bScribeCoin Signed Message:\n" + length + message
    return final
  
def Hash_Sha256(x):
    x = to_bytes(x, 'utf8')
    out = bytes(sha256(x))
    return out
  
def Hash(x):
    x = to_bytes(x, 'utf8')
    out = bytes(sha256(sha256(x)))
    return out

def rev_hex(s: str) -> str:
    return bh2u(bfh(s)[::-1])


def int_to_hex(i: int, length: int=1) -> str:
    """Converts int to little-endian hex string.
    `length` is the number of bytes available
    """
    if not isinstance(i, int):
        raise TypeError('{} instead of int'.format(i))
    range_size = pow(256, length)
    if i < -(range_size//2) or i >= range_size:
        raise OverflowError('cannot convert int {} to hex ({} bytes)'.format(i, length))
    if i < 0:
        # two's complement
        i = range_size + i
    s = hex(i)[2:].rstrip('L')
    s = "0"*(2*length - len(s)) + s
    return rev_hex(s)

def script_num_to_hex(i: int) -> str:
    """See CScriptNum in Bitcoin Core.
    Encodes an integer as hex, to be used in script.

    ported from https://github.com/bitcoin/bitcoin/blob/8cbc5c4be4be22aca228074f087a374a7ec38be8/src/script/script.h#L326
    """
    if i == 0:
        return ''

    result = bytearray()
    neg = i < 0
    absvalue = abs(i)
    while absvalue > 0:
        result.append(absvalue & 0xff)
        absvalue >>= 8

    if result[-1] & 0x80:
        result.append(0x80 if neg else 0x00)
    elif neg:
        result[-1] |= 0x80

    return bh2u(result)


from ecdsa.ecdsa import curve_secp256k1, generator_secp256k1
from ecdsa.curves import SECP256k1
from ecdsa.ellipticcurve import Point
from ecdsa.util import string_to_number, number_to_string

def verify_message(address, sig, message):
    assert_bytes(sig, message)
    try:
        h = Hash(msg_magic(message))
        public_key, compressed = pubkey_from_signature(sig, h)
        # check public key using the address
        pubkey = point_to_ser(public_key.pubkey.point, compressed)
        for txin_type in ['p2pkh','p2wpkh','p2wpkh-p2sh']:
            addr = pubkey_to_address(txin_type, bh2u(pubkey))
            if address == addr:
                break
        else:
            raise Exception("Bad signature")
        # check message
        public_key.verify_digest(sig[1:], h, sigdecode = ecdsa.util.sigdecode_string)
        return True
    except Exception as e:
        print_error("Verification error: {0}".format(e))
        return False


def encrypt_message(message, pubkey, magic):
    return EC_KEY.encrypt_message(message, bfh(pubkey), magic)


def chunks(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]


def ECC_YfromX(x,curved=curve_secp256k1, odd=True):
    _p = curved.p()
    _a = curved.a()
    _b = curved.b()
    for offset in range(128):
        Mx = x + offset
        My2 = pow(Mx, 3, _p) + _a * pow(Mx, 2, _p) + _b % _p
        My = pow(My2, (_p+1)//4, _p )

        if curved.contains_point(Mx,My):
            if odd == bool(My&1):
                return [My,offset]
            return [_p-My,offset]
    raise Exception('ECC_YfromX: No Y found')


def negative_point(P):
    return Point( P.curve(), P.x(), -P.y(), P.order() )


def point_to_ser(P, comp=True ):
    if comp:
        return bfh( ('%02x'%(2+(P.y()&1)))+('%064x'%P.x()) )
    return bfh( '04'+('%064x'%P.x())+('%064x'%P.y()) )


def ser_to_point(Aser):
    curve = curve_secp256k1
    generator = generator_secp256k1
    _r  = generator.order()
    assert Aser[0] in [0x02, 0x03, 0x04]
    if Aser[0] == 0x04:
        return Point( curve, string_to_number(Aser[1:33]), string_to_number(Aser[33:]), _r )
    Mx = string_to_number(Aser[1:])
    return Point( curve, Mx, ECC_YfromX(Mx, curve, Aser[0] == 0x03)[0], _r )

class MyVerifyingKey(ecdsa.VerifyingKey):
    @classmethod
    def from_signature(klass, sig, recid, h, curve):
        """ See http://www.secg.org/download/aid-780/sec1-v2.pdf, chapter 4.1.6 """
        from ecdsa import util, numbertheory
        from . import msqr
        curveFp = curve.curve
        G = curve.generator
        order = G.order()
        # extract r,s from signature
        r, s = util.sigdecode_string(sig, order)
        # 1.1
        x = r + (recid//2) * order
        # 1.3
        alpha = ( x * x * x  + curveFp.a() * x + curveFp.b() ) % curveFp.p()
        beta = msqr.modular_sqrt(alpha, curveFp.p())
        y = beta if (beta - recid) % 2 == 0 else curveFp.p() - beta
        # 1.4 the constructor checks that nR is at infinity
        R = Point(curveFp, x, y, order)
        # 1.5 compute e from message:
        e = string_to_number(h)
        minus_e = -e % order
        # 1.6 compute Q = r^-1 (sR - eG)
        inv_r = numbertheory.inverse_mod(r,order)
        Q = inv_r * ( s * R + minus_e * G )
        return klass.from_public_point( Q, curve )

def i2o_ECPublicKey(pubkey, compressed=False):
    # public keys are 65 bytes long (520 bits)
    # 0x04 + 32-byte X-coordinate + 32-byte Y-coordinate
    # 0x00 = point at infinity, 0x02 and 0x03 = compressed, 0x04 = uncompressed
    # compressed keys: <sign> <x> where <sign> is 0x02 if y is even and 0x03 if y is odd
    if compressed:
        if pubkey.point.y() & 1:
            key = '03' + '%064x' % pubkey.point.x()
        else:
            key = '02' + '%064x' % pubkey.point.x()
    else:
        key = '04' + \
              '%064x' % pubkey.point.x() + \
              '%064x' % pubkey.point.y()

    return bfh(key)
# end pywallet openssl private key implementation


def GetPubKey(pubkey, compressed=False):
    return i2o_ECPublicKey(pubkey, compressed)


def GetSecret(pkey):
    return bfh('%064x' % pkey.secret)


def is_compressed(sec):
    return deserialize_privkey(sec)[2]

def pubkey_from_signature(sig, h):
    if len(sig) != 65:
        raise Exception("Wrong encoding")
    nV = sig[0]
    if nV < 27 or nV >= 35:
        raise Exception("Bad encoding")
    if nV >= 31:
        compressed = True
        nV -= 4
    else:
        compressed = False
    recid = nV - 27
    return MyVerifyingKey.from_signature(sig[1:], recid, h, curve = SECP256k1), compressed


class MySigningKey(ecdsa.SigningKey):
    """Enforce low S values in signatures"""

    def sign_number(self, number, entropy=None, k=None):
        curve = SECP256k1
        G = curve.generator
        order = G.order()
        r, s = ecdsa.SigningKey.sign_number(self, number, entropy, k)
        if s > order//2:
            s = order - s
        return r, s



class EC_KEY(object):

    def __init__( self, k ):
        secret = string_to_number(k)
        self.pubkey = ecdsa.ecdsa.Public_key( generator_secp256k1, generator_secp256k1 * secret )
        self.privkey = ecdsa.ecdsa.Private_key( self.pubkey, secret )
        self.secret = secret

    def get_public_key(self, compressed=True):
        return bh2u(point_to_ser(self.pubkey.point, compressed))

    def sign(self, msg_hash):
        private_key = MySigningKey.from_secret_exponent(self.secret, curve = SECP256k1)
        public_key = private_key.get_verifying_key()
        signature = private_key.sign_digest_deterministic(msg_hash, hashfunc=hashlib.sha256, sigencode = ecdsa.util.sigencode_string)
        assert public_key.verify_digest(signature, msg_hash, sigdecode = ecdsa.util.sigdecode_string)
        return signature

    def sign_message(self, message, is_compressed):
        signature = self.sign(Hash(msg_magic(message)))
        for i in range(4):
            sig = bytes([27 + i + (4 if is_compressed else 0)]) + signature
            try:
                self.verify_message(sig, message)
                return sig
            except Exception as e:
                continue
        else:
            raise Exception("error: cannot sign message")


    def verify_message(self, sig, message):
        h = Hash(msg_magic(message))
        public_key, compressed = pubkey_from_signature(sig, h)
        # check public key
        if point_to_ser(public_key.pubkey.point, compressed) != point_to_ser(self.pubkey.point, compressed):
            raise Exception("Bad signature")
        print('>',public_key)
        # check message
        public_key.verify_digest(sig[1:], h, sigdecode = ecdsa.util.sigdecode_string)


    # ECIES encryption/decryption methods; AES-128-CBC with PKCS7 is used as the cipher; hmac-sha256 is used as the mac

    @classmethod
    def encrypt_message(self, message, pubkey):

        pk = ser_to_point(pubkey)
        if not ecdsa.ecdsa.point_is_valid(generator_secp256k1, pk.x(), pk.y()):
            raise Exception('invalid pubkey')

        ephemeral_exponent = number_to_string(ecdsa.util.randrange(pow(2,256)), generator_secp256k1.order())
        ephemeral = EC_KEY(ephemeral_exponent)
        ecdh_key = point_to_ser(pk * ephemeral.privkey.secret_multiplier)
        key = hashlib.sha512(ecdh_key).digest()
        iv, key_e, key_m = key[0:16], key[16:32], key[32:]
        ciphertext = aes_encrypt_with_iv(key_e, iv, message)
        ephemeral_pubkey = ephemeral.get_public_key(compressed=True).decode('hex')
        encrypted = magic_msg() + ephemeral_pubkey + ciphertext
        mac = hmac.new(key_m, encrypted, hashlib.sha256).digest()

        return base64.b64encode(encrypted + mac)


    def decrypt_message(self, encrypted):
        encrypted = base64.b64decode(encrypted)
        if len(encrypted) < 85:
            raise Exception('invalid ciphertext: length')
        magic = encrypted[:4]
        ephemeral_pubkey = encrypted[4:37]
        ciphertext = encrypted[37:-32]
        mac = encrypted[-32:]
        if magic != magic_msg():
            raise Exception('invalid ciphertext: invalid magic bytes')
        try:
            ephemeral_pubkey = ser_to_point(ephemeral_pubkey)
        except AssertionError as e:
            raise Exception('invalid ciphertext: invalid ephemeral pubkey')
        if not ecdsa.ecdsa.point_is_valid(generator_secp256k1, ephemeral_pubkey.x(), ephemeral_pubkey.y()):
            raise Exception('invalid ciphertext: invalid ephemeral pubkey')
        ecdh_key = point_to_ser(ephemeral_pubkey * self.privkey.secret_multiplier)
        key = hashlib.sha512(ecdh_key).digest()
        iv, key_e, key_m = key[0:16], key[16:32], key[32:]
        if mac != hmac.new(key_m, encrypted[:-32], hashlib.sha256).digest():
            raise InvalidPassword()
        return aes_decrypt_with_iv(key_e, iv, ciphertext)

def var_int(i: int) -> str:
    # https://en.bitcoin.it/wiki/Protocol_specification#Variable_length_integer
    if i<0xfd:
        return int_to_hex(i)
    elif i<=0xffff:
        return "fd"+int_to_hex(i,2)
    elif i<=0xffffffff:
        return "fe"+int_to_hex(i,4)
    else:
        return "ff"+int_to_hex(i,8)


def witness_push(item: str) -> str:
    """Returns data in the form it should be present in the witness.
    hex -> hex
    """
    return var_int(len(item) // 2) + item


def _op_push(i: int) -> str:
    if i < opcodes.OP_PUSHDATA1:
        return int_to_hex(i)
    elif i <= 0xff:
        return opcodes.OP_PUSHDATA1.hex() + int_to_hex(i, 1)
    elif i <= 0xffff:
        return opcodes.OP_PUSHDATA2.hex() + int_to_hex(i, 2)
    else:
        return opcodes.OP_PUSHDATA4.hex() + int_to_hex(i, 4)


def push_script(data: str) -> str:
    """Returns pushed data to the script, automatically
    choosing canonical opcodes depending on the length of the data.
    hex -> hex

    ported from https://github.com/btcsuite/btcd/blob/fdc2bc867bda6b351191b5872d2da8270df00d13/txscript/scriptbuilder.go#L128
    """
    data = bfh(data)
    data_len = len(data)

    # "small integer" opcodes
    if data_len == 0 or data_len == 1 and data[0] == 0:
        return opcodes.OP_0.hex()
    elif data_len == 1 and data[0] <= 16:
        return bh2u(bytes([opcodes.OP_1 - 1 + data[0]]))
    elif data_len == 1 and data[0] == 0x81:
        return opcodes.OP_1NEGATE.hex()

    return _op_push(data_len) + bh2u(data)


def add_number_to_script(i: int) -> bytes:
    return bfh(push_script(script_num_to_hex(i)))


def relayfee(network: 'Network' = None) -> int:
    from .simple_config import FEERATE_DEFAULT_RELAY, FEERATE_MAX_RELAY
    if network and network.relay_fee is not None:
        fee = network.relay_fee
    else:
        fee = FEERATE_DEFAULT_RELAY
    fee = min(fee, FEERATE_MAX_RELAY)
    fee = max(fee, 0)
    return fee


def dust_threshold(network: 'Network'=None) -> int:
    # Change <= dust threshold is added to the tx fee
    return 182 * 3 * relayfee(network) // 1000


def hash_encode(x: bytes) -> str:
    return bh2u(x[::-1])


def hash_decode(x: str) -> bytes:
    return bfh(x)[::-1]


############ functions from pywallet #####################

def hash160_to_b58_address(h160: bytes, addrtype: int) -> str:
    s = bytes([addrtype]) + h160
    s = s + sha256d(s)[0:4]
    return base_encode(s, base=58)


def b58_address_to_hash160(addr: str) -> Tuple[int, bytes]:
    addr = to_bytes(addr, 'ascii')
    _bytes = base_decode(addr, 25, base=58)
    return _bytes[0], _bytes[1:21]


def hash160_to_p2pkh(h160: bytes, *, net=None) -> str:
    if net is None: net = constants.net
    return hash160_to_b58_address(h160, net.ADDRTYPE_P2PKH)

def hash160_to_p2sh(h160: bytes, *, net=None) -> str:
    if net is None: net = constants.net
    return hash160_to_b58_address(h160, net.ADDRTYPE_P2SH)

def public_key_to_p2pkh(public_key: bytes, *, net=None) -> str:
    if net is None: net = constants.net
    return hash160_to_p2pkh(hash_160(public_key), net=net)

def hash_to_segwit_addr(h: bytes, witver: int, *, net=None) -> str:
    if net is None: net = constants.net
    return segwit_addr.encode(net.SEGWIT_HRP, witver, h)

def public_key_to_p2wpkh(public_key: bytes, *, net=None) -> str:
    if net is None: net = constants.net
    return hash_to_segwit_addr(hash_160(public_key), witver=0, net=net)

def script_to_p2wsh(script: str, *, net=None) -> str:
    if net is None: net = constants.net
    return hash_to_segwit_addr(sha256(bfh(script)), witver=0, net=net)

def p2wpkh_nested_script(pubkey: str) -> str:
    pkh = bh2u(hash_160(bfh(pubkey)))
    return '00' + push_script(pkh)

def p2wsh_nested_script(witness_script: str) -> str:
    wsh = bh2u(sha256(bfh(witness_script)))
    return '00' + push_script(wsh)

def pubkey_to_address(txin_type: str, pubkey: str, *, net=None) -> str:
    if net is None: net = constants.net
    if txin_type == 'p2pkh':
        return public_key_to_p2pkh(bfh(pubkey), net=net)
    elif txin_type == 'p2wpkh':
        return public_key_to_p2wpkh(bfh(pubkey), net=net)
    elif txin_type == 'p2wpkh-p2sh':
        scriptSig = p2wpkh_nested_script(pubkey)
        return hash160_to_p2sh(hash_160(bfh(scriptSig)), net=net)
    else:
        raise NotImplementedError(txin_type)

def redeem_script_to_address(txin_type: str, redeem_script: str, *, net=None) -> str:
    if net is None: net = constants.net
    if txin_type == 'p2sh':
        return hash160_to_p2sh(hash_160(bfh(redeem_script)), net=net)
    elif txin_type == 'p2wsh':
        return script_to_p2wsh(redeem_script, net=net)
    elif txin_type == 'p2wsh-p2sh':
        scriptSig = p2wsh_nested_script(redeem_script)
        return hash160_to_p2sh(hash_160(bfh(scriptSig)), net=net)
    else:
        raise NotImplementedError(txin_type)


def script_to_address(script: str, *, net=None) -> str:
    from .transaction import get_address_from_output_script
    t, addr = get_address_from_output_script(bfh(script), net=net)
    assert t == TYPE_ADDRESS
    return addr

def address_to_script(addr: str, *, net=None) -> str:
    if net is None: net = constants.net
    if not is_address(addr, net=net):
        raise BitcoinException(f"invalid bitcoin address: {addr}")
    #witver, witprog = segwit_addr.decode(net.SEGWIT_HRP, addr)
    #if witprog is not None:
    #    if not (0 <= witver <= 16):
    #        raise BitcoinException(f'impossible witness version: {witver}')
    #    script = bh2u(add_number_to_script(witver))
    #    script += push_script(bh2u(bytes(witprog)))
    #    return script
    addrtype, hash_160_ = b58_address_to_hash160(addr)
    if addrtype == net.ADDRTYPE_P2PKH:
        script = pubkeyhash_to_p2pkh_script(bh2u(hash_160_))
    elif addrtype in [net.ADDRTYPE_P2SH, net.ADDRTYPE_P2SH_ALT]:
        script = opcodes.OP_HASH160.hex()
        script += push_script(bh2u(hash_160_))
        script += opcodes.OP_EQUAL.hex()
    else:
        raise BitcoinException(f'unknown address type: {addrtype}')
    return script

def address_to_scripthash(addr: str) -> str:
    script = address_to_script(addr)
    return script_to_scripthash(script)

def script_to_scripthash(script: str) -> str:
    h = sha256(bfh(script))[0:32]
    return bh2u(bytes(reversed(h)))

def public_key_to_p2pk_script(pubkey: str) -> str:
    return push_script(pubkey) + opcodes.OP_CHECKSIG.hex()

def pubkeyhash_to_p2pkh_script(pubkey_hash160: str) -> str:
    script = bytes([opcodes.OP_DUP, opcodes.OP_HASH160]).hex()
    script += push_script(pubkey_hash160)
    script += bytes([opcodes.OP_EQUALVERIFY, opcodes.OP_CHECKSIG]).hex()
    return script


__b58chars = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
assert len(__b58chars) == 58

__b43chars = b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ$*+-./:'
assert len(__b43chars) == 43


def base_encode(v: bytes, base: int) -> str:
    """ encode v, which is a string of bytes, to base58."""
    assert_bytes(v)
    if base not in (58, 43):
        raise ValueError('not supported base: {}'.format(base))
    chars = __b58chars
    if base == 43:
        chars = __b43chars
    long_value = 0
    for (i, c) in enumerate(v[::-1]):
        long_value += (256**i) * c
    result = bytearray()
    while long_value >= base:
        div, mod = divmod(long_value, base)
        result.append(chars[mod])
        long_value = div
    result.append(chars[long_value])
    # Bitcoin does a little leading-zero-compression:
    # leading 0-bytes in the input become leading-1s
    nPad = 0
    for c in v:
        if c == 0x00:
            nPad += 1
        else:
            break
    result.extend([chars[0]] * nPad)
    result.reverse()
    return result.decode('ascii')


def base_decode(v: Union[bytes, str], length: Optional[int], base: int) -> Optional[bytes]:
    """ decode v into a string of len bytes."""
    # assert_bytes(v)
    v = to_bytes(v, 'ascii')
    if base not in (58, 43):
        raise ValueError('not supported base: {}'.format(base))
    chars = __b58chars
    if base == 43:
        chars = __b43chars
    long_value = 0
    for (i, c) in enumerate(v[::-1]):
        digit = chars.find(bytes([c]))
        if digit == -1:
            raise ValueError('Forbidden character {} for base {}'.format(c, base))
        long_value += digit * (base**i)
    result = bytearray()
    while long_value >= 256:
        div, mod = divmod(long_value, 256)
        result.append(mod)
        long_value = div
    result.append(long_value)
    nPad = 0
    for c in v:
        if c == chars[0]:
            nPad += 1
        else:
            break
    result.extend(b'\x00' * nPad)
    if length is not None and len(result) != length:
        return None
    result.reverse()
    return bytes(result)


class InvalidChecksum(Exception):
    pass


def EncodeBase58Check(vchIn: bytes) -> str:
    hash = sha256d(vchIn)
    return base_encode(vchIn + hash[0:4], base=58)


def DecodeBase58Check(psz: Union[bytes, str]) -> bytes:
    vchRet = base_decode(psz, None, base=58)
    payload = vchRet[0:-4]
    csum_found = vchRet[-4:]
    csum_calculated = sha256d(payload)[0:4]
    if csum_calculated != csum_found:
        raise InvalidChecksum(f'calculated {bh2u(csum_calculated)}, found {bh2u(csum_found)}')
    else:
        return payload


# backwards compat
# extended WIF for segwit (used in 3.0.x; but still used internally)
# the keys in this dict should be a superset of what Imported Wallets can import
WIF_SCRIPT_TYPES = {
    'p2pkh':0,
    'p2wpkh':1,
    'p2wpkh-p2sh':2,
    'p2sh':5,
    'p2wsh':6,
    'p2wsh-p2sh':7
}
WIF_SCRIPT_TYPES_INV = inv_dict(WIF_SCRIPT_TYPES)


def is_segwit_script_type(txin_type: str) -> bool:
    return txin_type in ('p2wpkh', 'p2wpkh-p2sh', 'p2wsh', 'p2wsh-p2sh')


def serialize_privkey(secret: bytes, compressed: bool, txin_type: str,
                      internal_use: bool=False) -> str:
    # we only export secrets inside curve range
    secret = ecc.ECPrivkey.normalize_secret_bytes(secret)
    if internal_use:
        prefix = bytes([(WIF_SCRIPT_TYPES[txin_type] + constants.net.WIF_PREFIX) & 255])
    else:
        prefix = bytes([constants.net.WIF_PREFIX])
    suffix = b'\01' if compressed else b''
    vchIn = prefix + secret + suffix
    base58_wif = EncodeBase58Check(vchIn)
    if internal_use:
        return base58_wif
    else:
        return '{}:{}'.format(txin_type, base58_wif)

def regenerate_key(pk):
    assert len(pk) == 32
    return EC_KEY(pk)

def public_key_from_private_key(pk, compressed):
    pkey = regenerate_key(pk)
    public_key = GetPubKey(pkey.pubkey, compressed)
    return bh2u(public_key)

def address_from_private_key(sec):
    txin_type, privkey, compressed = deserialize_privkey(sec)
    public_key = public_key_from_private_key(privkey, compressed)
    return pubkey_to_address(txin_type, public_key)

def deserialize_privkey(key: str) -> Tuple[str, bytes, bool]:
    if is_minikey(key):
        return 'p2pkh', minikey_to_private_key(key), False

    txin_type = None
    if ':' in key:
        txin_type, key = key.split(sep=':', maxsplit=1)
        if txin_type not in WIF_SCRIPT_TYPES:
            raise BitcoinException('unknown script type: {}'.format(txin_type))
    try:
        vch = DecodeBase58Check(key)
    except BaseException:
        neutered_privkey = str(key)[:3] + '..' + str(key)[-2:]
        raise BitcoinException("cannot deserialize privkey {}"
                               .format(neutered_privkey))

    if txin_type is None:
        # keys exported in version 3.0.x encoded script type in first byte
        prefix_value = vch[0] - constants.net.WIF_PREFIX
        try:
            txin_type = WIF_SCRIPT_TYPES_INV[prefix_value]
        except KeyError:
            raise BitcoinException('invalid prefix ({}) for WIF key (1)'.format(vch[0]))
    else:
        # all other keys must have a fixed first byte
        if vch[0] != constants.net.WIF_PREFIX:
            raise BitcoinException('invalid prefix ({}) for WIF key (2)'.format(vch[0]))
    
    if len(vch) not in [33, 34]:
        raise BitcoinException('invalid vch len for WIF key: {}'.format(len(vch)))
    compressed = len(vch) == 34
    return txin_type, vch[1:33], compressed



def is_compressed_privkey(sec: str) -> bool:
    return deserialize_privkey(sec)[2]


def address_from_private_key(sec: str) -> str:
    txin_type, privkey, compressed = deserialize_privkey(sec)
    public_key = ecc.ECPrivkey(privkey).get_public_key_hex(compressed=compressed)
    return pubkey_to_address(txin_type, public_key)

def is_segwit_address(addr: str, *, net=None) -> bool:
    if net is None: net = constants.net
    try:
        witver, witprog = segwit_addr.decode(net.SEGWIT_HRP, addr)
    except Exception as e:
        return False
    return witprog is not None

def is_b58_address(addr: str, *, net=None) -> bool:
    if net is None: net = constants.net
    try:
        addrtype, h = b58_address_to_hash160(addr)
    except Exception as e:
        return False
    if addrtype not in [net.ADDRTYPE_P2PKH, net.ADDRTYPE_P2SH, net.ADDRTYPE_P2SH_ALT]:
        return False
    return addr == hash160_to_b58_address(h, addrtype)

def is_address(addr: str, *, net=None) -> bool:
    if net is None: net = constants.net
    return is_segwit_address(addr, net=net) \
           or is_b58_address(addr, net=net)


def is_private_key(key: str, *, raise_on_error=False) -> bool:
    try:
        deserialize_privkey(key)
        return True
    except BaseException as e:
        if raise_on_error:
            raise
        return False


########### end pywallet functions #######################

def is_minikey(text: str) -> bool:
    # Minikeys are typically 22 or 30 characters, but this routine
    # permits any length of 20 or more provided the minikey is valid.
    # A valid minikey must begin with an 'S', be in base58, and when
    # suffixed with '?' have its SHA256 hash begin with a zero byte.
    # They are widely used in Casascius physical bitcoins.
    return (len(text) >= 20 and text[0] == 'S'
            and all(ord(c) in __b58chars for c in text)
            and sha256(text + '?')[0] == 0x00)

def minikey_to_private_key(text: str) -> bytes:
    return sha256(text)
