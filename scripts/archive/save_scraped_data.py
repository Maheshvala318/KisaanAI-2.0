import pandas as pd
import json

data = [
  {
    "name": "State Agriculture Thesis Grant for M.Sc. Agriculture",
    "ministry": "Department of Agriculture, Government of Nagaland",
    "benefits": "Provides a thesis grant to students based on the agricultural course/programme in which they are enrolled.",
    "eligibility": "Inhabitants of Nagaland who have passed the M.Sc. Agriculture programme. The institution must have a valid AISHE/UDISE code, and the applicant must not be a beneficiary of any other scholarship."
  },
  {
    "name": "State Agriculture Scholarship for B.Sc. & M.Sc. Agriculture",
    "ministry": "Department of Agriculture, Government of Nagaland",
    "benefits": "Offers financial scholarships to students pursuing undergraduate or postgraduate studies in agriculture.",
    "eligibility": "Inhabitants of Nagaland who have passed Class 12th (for B.Sc.) or B.Sc. Ag. (for M.Sc.). Applicants must study in an institution with a valid AISHE/UDISE code."
  },
  {
    "name": "Agriculture Academic Studies Scheme",
    "ministry": "Department of Agriculture & Farmers’ Welfare, Government of Meghalaya",
    "benefits": "Sponsors students for 4-year Graduate/degree courses in Agriculture or Horticulture against state quota seats in recognized Agricultural Universities.",
    "eligibility": "Permanent residents of Meghalaya who have qualified for the state quota seats in respective universities."
  },
  {
    "name": "Use of Advanced Drone Technology (Agriculture Aircraft) in Agriculture Sector",
    "ministry": "Agriculture, Farmers Welfare and Cooperation Department, Gujarat",
    "benefits": "Financial assistance for the use of drones to spray crop protection chemicals and bio-fertilizers, enhancing precision and safety.",
    "eligibility": "Farmers belonging to the state of Gujarat."
  },
  {
    "name": "Sardar Patel Agriculture Research Award",
    "ministry": "Department of Agriculture, Farmers Welfare & Co-operation, Government of Gujarat",
    "benefits": "Awards in five different categories to recognize and incentivize farmers for innovative agricultural practices and high yields.",
    "eligibility": "Farmers of Gujarat state who demonstrate innovative ideas and exceptional productivity in their farming practices."
  },
  {
    "name": "Meghalaya Agriculture Response Vehicle Scheme",
    "ministry": "Department of Agriculture & Farmers’ Welfare, Government of Meghalaya",
    "benefits": "Provides a 50% subsidy on the cost of a vehicle (up to ₹2 lakhs) to facilitate the transport of agricultural produce to markets.",
    "eligibility": "Individual farmers, groups of farmers, cooperatives, or registered agricultural associations in Meghalaya."
  },
  {
    "name": "National Agriculture Insurance Scheme (NAIS)",
    "ministry": "Ministry of Agriculture and Farmers Welfare, Government of India",
    "benefits": "Comprehensive insurance coverage and financial support to farmers in case of failure of notified crops due to natural calamities, pests, and diseases.",
    "eligibility": "All farmers, including sharecroppers and tenant farmers, growing the notified crops in the notified areas."
  },
  {
    "name": "National Mission for Sustainable Agriculture - Reinforced Area Development",
    "ministry": "Ministry of Agriculture and Farmers Welfare (implemented by States)",
    "benefits": "Promotes integrated farming systems for enhancing livelihood and productivity, especially in rain-fed areas.",
    "eligibility": "Small and marginal farmers in selected clusters or development areas defined by the state."
  },
  {
    "name": "Basic Agriculture Training Centre Scheme",
    "ministry": "Department of Agriculture & Farmers’ Welfare, Government of Meghalaya",
    "benefits": "Offers vocational training and skill development in various agriculture-related fields to rural youth and farmers.",
    "eligibility": "Youth and farmers who are permanent residents of Meghalaya."
  },
  {
    "name": "Interest Subsidy on Loans for Agriculture and Allied Activities",
    "ministry": "Government of Goa",
    "benefits": "Subsidizes the interest on short-term and long-term loans taken for agricultural purposes to reduce the financial burden on farmers.",
    "eligibility": "Farmers and agriculturalists residing and farming in the state of Goa."
  },
  {
    "name": "Dr. S.K. Mukherjee Scholarship for B.Sc. Agriculture Students",
    "ministry": "Government of Uttarakhand",
    "benefits": "A one-year scholarship of ₹1,100 per month provided to meritorious students.",
    "eligibility": "Meritorious students currently in their 2nd or 3rd year of a B.Sc. Agriculture course in Uttarakhand."
  },
  {
    "name": "Priyank Pathak Scholarship for B.Sc. Agriculture (4th Year) Students",
    "ministry": "Government of Uttarakhand",
    "benefits": "A one-year scholarship of ₹800 per month awarded to support agricultural education.",
    "eligibility": "Meritorious students in their 4th year of study for the B.Sc. Agriculture degree in Uttarakhand."
  },
  {
    "name": "Asian Agri-History Foundation Research Fellowship (M.Sc. Agriculture)",
    "ministry": "Government of Uttarakhand",
    "benefits": "A fellowship of ₹1,200 per month for one year to support advanced agricultural research.",
    "eligibility": "Meritorious students pursuing M.Sc. in Agriculture across all disciplines in the state of Uttarakhand."
  },
  {
    "name": "Dr. A.N. Mukhopadhyay Needy Student Fund (B.Sc. Agriculture)",
    "ministry": "Government of Uttarakhand",
    "benefits": "Financial assistance to underprivileged students to help them complete their agricultural education.",
    "eligibility": "Needy final year students of the B.Sc. Agriculture programme in Uttarakhand."
  },
  {
    "name": "Dr. K.C. Sharma Fellowship (M.Sc. Agriculture, Agronomy)",
    "ministry": "Government of Uttarakhand",
    "benefits": "Monthly fellowship of ₹1,200 for one year awarded to students specializing in Agronomy.",
    "eligibility": "Meritorious students in their 2nd year of the M.Sc. Agriculture (Agronomy) course in Uttarakhand."
  },
  {
    "name": "Merit-cum-Means Scholarships For Under Graduate Studies",
    "ministry": "Ministry of Agriculture and Farmers Welfare, Govt of India",
    "benefits": "Provides financial aid to students from economically weaker sections to pursue various branches of agriculture and animal science.",
    "eligibility": "Undergraduate students with high academic merit whose total family income is below the specified threshold."
  },
  {
    "name": "Integrated Technology Enabled Agriculture Management System (iTEAMS)",
    "ministry": "Department of Agriculture & Farmers’ Welfare, Government of Meghalaya",
    "benefits": "Technology-based logistics and advisory support system that helps farmers with market linkages and agricultural information.",
    "eligibility": "Registered farmers and agricultural stakeholders in the state of Meghalaya."
  },
  {
    "name": "Primary Cooperative Agriculture and Rural Development Bank: For Minor Irrigation",
    "ministry": "Government of Gujarat",
    "benefits": "Loans provided for minor irrigation activities like digging wells, installing pump sets, and building check dams.",
    "eligibility": "Farmers in Gujarat seeking to improve their irrigation infrastructure for better crop yield."
  },
  {
    "name": "Chief Minister’s Solar Power Pump Scheme",
    "ministry": "Government of Gujarat",
    "benefits": "Highly subsidized installation of solar-powered water pumps for irrigation, reducing dependence on electricity and diesel.",
    "eligibility": "Farmers in the state of Gujarat who have valid land ownership and an existing water source."
  },
  {
    "name": "Promotion of Agricultural Mechanization for In-Situ Management of Crop Residue",
    "ministry": "Ministry of Agriculture and Farmers Welfare, Govt of India",
    "benefits": "Subsidies for the purchase of machinery required to manage crop residue (stubble) within the field to prevent stubble burning.",
    "eligibility": "Individual farmers, cooperative societies of farmers, and entrepreneurs in the states of Punjab, Haryana, Uttar Pradesh, and NCT of Delhi."
  }
]

df = pd.DataFrame(data)
# Add search_text field for FAISS
df['search_text'] = df['name'] + " " + df['benefits'] + " " + df['eligibility']
df.to_csv("dataset/schemes_india.csv", index=False)
print(f"Successfully saved {len(df)} schemes to dataset/schemes_india.csv")
