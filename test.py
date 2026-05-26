import pandas as pd

# ================================
# LOAD FILE
# ================================
# change to your file path
file_path = "data.xlsx"

df = pd.read_excel(file_path)

# normalize column names (optional safety)
df.columns = df.columns.str.strip().str.lower()

# expected columns:
# agent_msisdn, customer, package_amount

# ================================
# RULE 1: Agent = Customer (INVALID)
# ================================
df["invalid_agent_customer"] = df["agent_msisdn"] == df["customer"]

# ================================
# RULE 2: Customer duplicate reward
# ================================
df["customer_count"] = df.groupby("customer")["customer"].transform("count")
df["duplicate_customer"] = df["customer_count"] > 1

# ================================
# RULE 3: Agent-Customer duplicate
# ================================
df["agent_customer_count"] = df.groupby(["agent_msisdn", "customer"])["customer"].transform("count")
df["duplicate_agent_customer"] = df["agent_customer_count"] > 1

# ================================
# FINAL VIOLATION FLAG
# ================================
df["violation"] = (
    df["invalid_agent_customer"] |
    df["duplicate_customer"] |
    df["duplicate_agent_customer"]
)

# ================================
# 📊 SUMMARY
# ================================
total_rows = len(df)

invalid_agent_customer_count = df["invalid_agent_customer"].sum()
duplicate_customer_count = df["duplicate_customer"].sum()
duplicate_agent_customer_count = df["duplicate_agent_customer"].sum()

total_violations = df["violation"].sum()

# total wrong resource
total_wrong_resource = df.loc[df["violation"], "package_amount"].sum()

print("\n===== SUMMARY =====")
print(f"Total rows: {total_rows}")
print(f"Agent = Customer violations: {invalid_agent_customer_count}")
print(f"Duplicate customer rewards: {duplicate_customer_count}")
print(f"Duplicate agent-customer: {duplicate_agent_customer_count}")
print(f"Total violations: {total_violations}")
print(f"Total wrong resource (MB): {total_wrong_resource}")

# ================================
# 📋 LISTS
# ================================

# Customers who received multiple rewards
duplicate_customers = df[df["duplicate_customer"]]["customer"].unique()

# Agents with duplicate issues
problem_agents = df[df["duplicate_agent_customer"]]["agent_msisdn"].unique()

print("\nCustomers with multiple rewards:")
print(duplicate_customers)

print("\nAgents with duplicate reward issues:")
print(problem_agents)

# ================================
# 💰 RESOURCE PER CUSTOMER
# ================================
customer_summary = df.groupby("customer")["package_amount"].sum().reset_index()
customer_summary = customer_summary.sort_values(by="package_amount", ascending=False)

print("\nTop customers by received resource:")
print(customer_summary.head())

# ================================
# SAVE CLEANED RESULT
# ================================
df.to_excel("validated_output.xlsx", index=False)

print("\n✅ Output saved to validated_output.xlsx")