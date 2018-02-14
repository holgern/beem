from steem.instance import shared_steem_instance
from .account import Account
from .exceptions import WorkerDoesNotExistsException
from .utils import formatTimeString
from .blockchainobject import BlockchainObject


class Worker(BlockchainObject):
    """ Read data about a worker in the chain

        :param str id: id of the worker
        :param steem steem_instance: Steem() instance to use when
            accesing a RPC

    """
    type_id = 14

    def refresh(self):
        worker = self.steem.rpc.get_object(self.identifier)
        if not worker:
            raise WorkerDoesNotExistsException
        worker["work_end_date"] = formatTimeString(worker["work_end_date"])
        worker["work_begin_date"] = formatTimeString(worker["work_begin_date"])
        super(Worker, self).__init__(worker, steem_instance=self.steem)
        self.cached = True

    @property
    def account(self):
        return Account(
            self["worker_account"], steem_instance=self.steem)


class Workers(list):
    """ Obtain a list of workers for an account

        :param str account_name/id: Name/id of the account (optional)
        :param steem steem_instance: Steem() instance to use when
            accesing a RPC
    """
    def __init__(self, account_name=None, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        if account_name:
            account = Account(account_name, steem_instance=self.steem)
            self.workers = self.steem.rpc.get_workers_by_account(
                account["id"])
        else:
            self.workers = self.steem.rpc.get_all_workers()

        super(Workers, self).__init__(
            [
                Worker(x, lazy=True, steem_instance=self.steem)
                for x in self.workers
            ]
        )
