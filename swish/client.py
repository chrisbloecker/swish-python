import warnings

import requests

from .environment import Environment
from .exceptions import SwishError
from .models import Payment, Refund, CommerceQRCodeRequest, Operation

try:
    from requests.packages.urllib3.contrib import pyopenssl
    pyopenssl.extract_from_urllib3()
except ImportError:
    pass


class SwishClient(object):
    def __init__(self, environment, merchant_swish_number, cert, verify=False):
        self.environment = Environment.parse_environment(environment)
        self.merchant_swish_number = merchant_swish_number
        self.cert = cert
        self.verify = verify

    def __put(self, endpoint, payload):
        if endpoint == 'commerce':
          base_url = self.environment.qr_url
        else:
          base_url = self.environment.base_url
        url = base_url + endpoint
        return requests.put( url     = url
                           , json    = payload
                           , headers = {'Content-Type' : 'application/json'}
                           , cert    = self.cert
                           , verify  = self.verify
                           )

    # def post(self, endpoint, payload):
    #     warnings.warn("You shouldn't be calling this method. It will be private in a future version.", DeprecationWarning)
    #     self.__post(endpoint, payload)

    def __get(self, endpoint, parameter):
        url = self.environment.base_url + endpoint + '/' + str(parameter)
        return requests.get( url    = url
                           , cert   = self.cert
                           , verify = self.verify
                           )

    # def get(self, endpoint, parameter):
    #     warnings.warn("You shouldn't be calling this method. It will be private in a future version.", DeprecationWarning)
    #     self.__get(endpoint, parameter)

    def __patch(self, endpoint, parameter, payload):
        url = self.environment.base_url + endpoint + '/' + str(parameter)
        return requests.patch( url     = url
                             , json    = payload
                             , headers = {'Content-Type' : 'application/json-patch+json'}
                             , cert    = self.cert
                             , verify  = self.verify
                             )


    def create_payment( self
                      , amount
                      , currency
                      , callback_url
                      , instructionUUID
                      , payee_payment_reference = None
                      , message                 = None
                      , payer_alias             = None
                      ):
        payment_request = Payment({ 'payee_alias'             : self.merchant_swish_number
                                  , 'amount'                  : amount
                                  , 'currency'                : currency
                                  , 'callback_url'            : callback_url
                                  , 'callback_identifier'     : instructionUUID
                                  , 'payee_payment_reference' : payee_payment_reference
                                  , 'message'                 : message
                                  , 'payer_alias'             : payer_alias
                                  })

        response = self.__put(f'v2/paymentrequests/{instructionUUID}', payment_request.to_primitive())
        if response.status_code == 422:
            raise SwishError(response.json())
        response.raise_for_status()

        return Payment({ 'id'            : response.headers.get('Location').split('/')[-1]
                       , 'location'      : response.headers.get('Location')
                       , 'request_token' : response.headers.get('PaymentRequestToken')
                       })

    def get_payment(self, payment_request_id):
        response = self.__get('v1/paymentrequests', payment_request_id)
        response.raise_for_status()
        return Payment(response.json())

    def cancel_payment(self, payment_request_id):
        operation = Operation()
        response = self.__patch('v1/paymentrequests', payment_request_id, [operation.to_primitive()])
        response.raise_for_status()
        return Payment(response.json())

    def create_refund( self
                     , original_payment_reference
                     , amount
                     , currency
                     , callback_url
                     , instructionUUID
                     , payer_payment_reference = None
                     , payment_reference       = None
                     , payee_alias             = None
                     , message                 = None
                     ):
        refund_request = Refund({ 'payer_alias': self.merchant_swish_number
                                , 'payee_alias': payee_alias
                                , 'original_payment_reference' : original_payment_reference
                                , 'amount'                     : amount
                                , 'currency'                   : currency
                                , 'callback_url'               : callback_url
                                , 'callback_identifier'        : instructionUUID
                                , 'payer_payment_reference'    : payer_payment_reference
                                , 'payment_reference'          : payment_reference
                                , 'message'                    : message
                                })

        response = self.__put(f'v2/refunds/{instructionUUID}', refund_request.to_primitive())
        if response.status_code == 422:
            raise SwishError(response.json())
        response.raise_for_status()

        return Refund({ 'id'       : response.headers.get('Location').split('/')[-1]
                      , 'location' : response.headers.get('Location')
                      })

    def get_refund(self, refund_id):
        response = self.__get('v1/refunds', refund_id)
        response.raise_for_status()
        return Refund(response.json())


    # not for now.
    def commerce_qr_code( self
                        , token
                        , format
                        , size        = None
                        , border      = None
                        , transparent = None
                        ):
        commerce_qr_code_request = CommerceQRCodeRequest({ 'token'       : token
                                                         , 'format'      : format
                                                         , 'size'        : size
                                                         , 'border'      : border
                                                         , 'transparent' : transparent
                                                         })

        response = self.__put('commerce', commerce_qr_code_request.to_primitive())
        response.raise_for_status()
        return response.content
