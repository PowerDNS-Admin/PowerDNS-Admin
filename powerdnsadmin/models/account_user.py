from .base import db


class AccountUser(db.Model):
    __tablename__ = 'account_user'
    __table_args__ = (
        db.Index('ix_account_user_user_id_account_id',
                 'user_id', 'account_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer,
                           db.ForeignKey('account.id'),
                           nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, account_id, user_id):
        self.account_id = account_id
        self.user_id = user_id

    def __repr__(self):
        return '<Account_User {0} {1}>'.format(self.account_id, self.user_id)
