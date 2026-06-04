from sqlpyhelper.automation_utils import AutomationUtils

utils = AutomationUtils()

print("✅ Loading test data...")
utils.load_data_from_csv("sample_data.csv", "contributors")

print("\n📊 Contribution breakdown:")
print(utils.aggregate_column("contributors", "contribution", "name", "timestamp"))

print("\n⚠️ Missing months:")
print(utils.detect_missing_periods("contributors", "name", "timestamp"))

print("\n🚨 Outliers:")
print(utils.detect_outliers("contributors", "contribution"))
