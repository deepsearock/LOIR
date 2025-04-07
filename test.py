import datetime
import random
import sys
import logging

class InsufficientFundsError(Exception):
    pass

class Account:
    def __init__(self, owner, balance=0.0):
        self.owner = owner
        self.balance = balance
        self.transactions = []

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        self.transactions.append(("deposit", amount, datetime.datetime.now()))
        logging.info(f"{self.owner} deposited {amount}. New balance: {self.balance}")

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.balance:
            raise InsufficientFundsError(f"Insufficient funds for {self.owner}")
        self.balance -= amount
        self.transactions.append(("withdraw", amount, datetime.datetime.now()))
        logging.info(f"{self.owner} withdrew {amount}. New balance: {self.balance}")

    def get_balance(self):
        return self.balance

    def get_transaction_history(self):
        return self.transactions

class Bank:
    def __init__(self, name):
        self.name = name
        self.accounts = {}

    def create_account(self, owner, initial_deposit=0.0):
        if owner in self.accounts:
            raise ValueError("Account already exists")
        account = Account(owner, initial_deposit)
        self.accounts[owner] = account
        logging.info(f"Created account for {owner} with initial deposit {initial_deposit}")
        return account

    def get_account(self, owner):
        return self.accounts.get(owner)

    def transfer(self, from_owner, to_owner, amount):
        from_account = self.get_account(from_owner)
        to_account = self.get_account(to_owner)
        if not from_account or not to_account:
            raise ValueError("One or both accounts do not exist")
        from_account.withdraw(amount)
        to_account.deposit(amount)
        logging.info(f"Transferred {amount} from {from_owner} to {to_owner}")

    def print_accounts(self):
        print(f"--- Accounts at {self.name} ---")
        for owner, account in self.accounts.items():
            print(f"Account: {owner}, Balance: {account.get_balance()}")

def simulate_bank_operations():
    bank = Bank("Global Bank")
    try:
        alice = bank.create_account("Alice", 1000.0)
        bob = bank.create_account("Bob", 500.0)
        charlie = bank.create_account("Charlie", 750.0)
    except ValueError as e:
        print("Error creating account:", e)
        return

    operations = [
        lambda: alice.deposit(200),
        lambda: bob.withdraw(100),
        lambda: bank.transfer("Alice", "Bob", 150),
        lambda: charlie.deposit(300),
        lambda: bank.transfer("Charlie", "Alice", 100),
        lambda: bob.withdraw(700)
    ]

    for op in operations:
        try:
            op()
        except InsufficientFundsError as e:
            print("Transaction failed:", e)
        except Exception as e:
            print("Error:", e)

    bank.print_accounts()
    return bank

def advanced_report(bank):
    print("\n--- Advanced Report ---")
    for owner, account in bank.accounts.items():
        print(f"\nAccount Owner: {owner}")
        print(f"Balance: {account.get_balance()}")
        print("Transactions:")
        for t in account.get_transaction_history():
            t_type, amount, timestamp = t
            print(f"  {timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {t_type} of {amount}")

def interactive_mode(bank):
    print("\nInteractive Mode. Type 'exit' to quit.")
    while True:
        command = input("Enter command (deposit, withdraw, transfer, report): ").strip().lower()
        if command == "exit":
            break
        elif command == "deposit":
            owner = input("Owner: ").strip()
            try:
                amount = float(input("Amount: ").strip())
            except ValueError:
                print("Invalid amount.")
                continue
            account = bank.get_account(owner)
            if account:
                try:
                    account.deposit(amount)
                    print("Deposit successful.")
                except Exception as e:
                    print("Error:", e)
            else:
                print("Account not found.")
        elif command == "withdraw":
            owner = input("Owner: ").strip()
            try:
                amount = float(input("Amount: ").strip())
            except ValueError:
                print("Invalid amount.")
                continue
            account = bank.get_account(owner)
            if account:
                try:
                    account.withdraw(amount)
                    print("Withdrawal successful.")
                except Exception as e:
                    print("Error:", e)
            else:
                print("Account not found.")
        elif command == "transfer":
            from_owner = input("From: ").strip()
            to_owner = input("To: ").strip()
            try:
                amount = float(input("Amount: ").strip())
            except ValueError:
                print("Invalid amount.")
                continue
            try:
                bank.transfer(from_owner, to_owner, amount)
                print("Transfer successful.")
            except Exception as e:
                print("Error:", e)
        elif command == "report":
            advanced_report(bank)
        else:
            print("Unknown command.")

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    bank = simulate_bank_operations()
    if bank is not None:
        interactive_mode(bank)

if __name__ == "__main__":
    main()
