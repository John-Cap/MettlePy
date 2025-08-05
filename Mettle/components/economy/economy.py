import random
import networkx as nx

def pingPythia():
    return "Hello from Mettle.economy!"

class Node:
    """Represents a financial entity (e.g., business, criminal group, regulator)."""
    def __init__(self, name, base_income=5000, base_expenses=5000):
        self.name = name
        self.income = base_income
        self.expenses = base_expenses
        self.connections = {}  # Stores financial relationships
        self.threats = {}  # {Threat: Counteraction}
    
    def add_connection(self, target_node, modifier, amount):
        """Creates a financial connection to another node and updates financial values."""
        self.connections[target_node.name] = {"modifier": modifier, "amount": amount}
        
        # Apply financial impact immediately
        if amount > 0:
            self.income += amount  # This node gains money
            target_node.expenses += amount  # The receiving node increases expenses
        else:
            self.expenses -= amount  # Outflow reduces available money
            target_node.income -= amount  # Receiving node loses money

    def apply_financial_change(self):
        """Calculates new balance based on financial modifications."""
        return self.income - self.expenses

    def react_to_threat(self, economy):
        """Triggers counteractions when suffering financial losses."""
        if self.apply_financial_change() < 0:
            print(f"⚠ {self.name} is struggling! Seeking counteraction...")
            if self.threats:
                threat, counter = random.choice(list(self.threats.items()))
                print(f"🔄 {self.name} responds with '{counter}'!")
                
                # Apply counteraction effect dynamically
                economy.add_connector(counter, self.name, threat, -random.randint(1000, 5000))

# TODO - Move to shared
class EconomyNetwork:
    """Manages the financial network and auto-balances responses."""
    def __init__(self):
        self.nodes = {}
        self.network = nx.DiGraph()

    def add_node(self, name, base_income=5000, base_expenses=5000):
        """Creates and stores a financial node."""
        node = Node(name, base_income, base_expenses)
        self.nodes[name] = node
        self.network.add_node(name)
        return node
    
    def getGlobalCashFlow(self):
        totalIn=0
        totalOut=0
        for val in self.nodes.values():
            totalIn+=val.income
            totalOut+=val.expenses
        deficit=totalIn-totalOut
        return [totalIn,totalOut,deficit]


    def add_connector(self, name, source, target, financial_impact):
        """Creates a financial relationship between two nodes and updates values."""
        if source in self.nodes and target in self.nodes:
            self.nodes[source].add_connection(self.nodes[target], name, financial_impact)
            self.network.add_edge(source, target, weight=financial_impact)
            print(f"💰 Connection Added: {source} → {target} [{name}: ${financial_impact}]")

    def auto_balance(self):
        """Checks for struggling nodes and triggers counteractions."""
        for node in self.nodes.values():
            node.react_to_threat(self)

class Player:
    """Handles player actions, investments, and decision-making."""
    def __init__(self, name, starting_cash=100000):
        self.name = name
        self.cash = starting_cash

    def invest(self, economy, source, target, action, amount):
        """Invests money in a financial action with risk/reward."""
        if amount > self.cash:
            print("❌ Not enough cash to invest!")
            return False

        risk = random.randint(1, 10)  # Simulating a dice roll
        print(f"🎲 Player invests ${amount} in {action} (Risk roll: {risk})")

        # Risk-based outcomes
        if risk > 7:
            profit = amount * 1.5
            print(f"✔ Success! Earned ${profit}.")
            self.cash += profit
        elif 4 <= risk <= 7:
            profit = amount * 0.5
            print(f"⚠ Partial success. Earned ${profit}.")
            self.cash += profit
        else:
            print(f"❌ Failure! Investment lost.")
            self.cash -= amount

        # Apply transaction effects to network
        economy.add_connector(action, source, target, amount)
        economy.auto_balance()  # Nodes react dynamically

if __name__ == "__main__":
    # Initialize Economy
    economy = EconomyNetwork()

    # Create Nodes5
    bakery = economy.add_node("Bakery", 5000, 5000)
    mafia = economy.add_node("Mafia", 7000, 5000)
    regulator = economy.add_node("Regulatory Agency", 10000, 5000)
    player_hq = economy.add_node("Player HQ", 10000, 5000)

    # Define Threats & Counteractions
    bakery.threats = {"Theft": "Protection Money", "Low Quality Flour": "Regulatory Crackdown"}
    mafia.threats = {"Snitching": "Bribery"}

    # Establish Initial Equilibrium
    economy.add_connector("Sales Revenue", "Bakery", "Player HQ", 3000)
    economy.add_connector("Protection Money", "Bakery", "Mafia", -2000)

    # Add Player
    player = Player("Bob")

    # Game Loop
    while True:
        state=economy.getGlobalCashFlow()
        print("//////////////////////////////////////")
        print(f"Economy state in/out/deficit: {state}")
        print("\n--- Player Turn ---")
        print(f"💰 Cash: ${player.cash}")

        # Display Current Monetary States
        print("\n🔎 Financial Overview:")
        for node_name, node in economy.nodes.items():
            print(f"{node_name}: Income=${node.income}, Expenses=${node.expenses}, Balance=${node.apply_financial_change()}")

        # Available Actions
        print("\nChoose an action:")
        print("1. Sell Dodgy Flour (Bakery → Player) | Risk: 40% | Potential: $5,000")
        print("2. Loan Sharking (Customers → Player) | Risk: 30% | Potential: $3,000")
        print("3. Arms Dealing (Military Depot → Player) | Risk: 50% | Potential: $8,000")
        print("4. Quit")

        choice = input("Select an action (1-4): ")

        if choice == "1":
            player.invest(economy, "Bakery", "Player HQ", "Sell Dodgy Flour", 5000)
        elif choice == "2":
            player.invest(economy, "Customers", "Player HQ", "Loan Sharking", 3000)
        elif choice == "3":
            player.invest(economy, "Military Depot", "Player HQ", "Arms Dealing", 8000)
        elif choice == "4":
            print("Exiting Game.")
            break
        else:
            print("Invalid selection.")
