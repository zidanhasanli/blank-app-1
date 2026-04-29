from openai import OpenAI
import pandas as pd
import matplotlib.pyplot as plt

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

print("This system helps student organizations choose the best event strategy using AI advisors.\n")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",  
    api_key="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"
)


def select_organization():
    print("\nSelect organization type:")
    print("1. Student Organization")
    print("2. Business Company")
    print("3. Nonprofit Organization")
    print("4. University Department")

    choice = input("\nEnter choice (1-4): ")

    if choice == "1":
        return "student"
    elif choice == "2":
        return "business"
    elif choice == "3":
        return "nonprofit"
    elif choice == "4":
        return "university"
    else:
        print("Invalid choice. Defaulting to Student Organization.")
        return "student"

def load_event_data(org_type):

    if org_type == "student":
        data = pd.DataFrame({
            'event_type': ['Workshop','Networking Event','Hackathon','Career Fair'],
            'avg_cost': [100,120,200,180],
            'avg_attendance': [50,110,150,140],
            'member_satisfaction': [9,8,9,8],
            'organization_difficulty': [2,3,4,3],
        })

    elif org_type == "business":
        data = pd.DataFrame({
            'event_type': ['Product Launch','Marketing Campaign','Customer Event','Employee Training'],
            'avg_cost': [300,200,150,100],
            'avg_attendance': [200,180,120,90],
            'member_satisfaction': [9,8,8,9],
            'organization_difficulty': [5,3,2,1],
        })

    elif org_type == "nonprofit":
        data = pd.DataFrame({
            'event_type': ['Fundraising Event','Volunteer Campaign','Awareness Campaign','Community Workshop'],
            'avg_cost': [150,80,60,50],
            'avg_attendance': [200,140,180,90],
            'member_satisfaction': [9,8,7,9],
            'organization_difficulty': [4,2,2,1],
        })

    elif org_type == "university":
        data = pd.DataFrame({
            'event_type': ['Research Seminar','Guest Lecture','Industry Panel','Career Fair'],
            'avg_cost': [120,100,140,180],
            'avg_attendance': [80,100,130,160],
            'member_satisfaction': [9,8,8,9],
            'organization_difficulty': [2,2,3,4],
        })

    summary = data.set_index("event_type")
    return summary

def get_advisors(org_type):

    if org_type == "student":
        return [
            "Treasury Advisor (focus on budget efficiency)",
            "Marketing Advisor (focus on engagement and recruitment)",
            "Member Experience Advisor (focus on member satisfaction)",
            "Logistics Advisor (focus on scheduling and feasibility)",
            "Faculty Advisor (focus on university policy and long-term value)"
        ]

    elif org_type == "business":
        return [
            "Finance Advisor (focus on cost and ROI)",
            "Marketing Advisor (focus on customer engagement)",
            "Operations Advisor (focus on execution feasibility)",
            "HR Advisor (focus on employee impact)",
            "Strategy Advisor (focus on long-term business value)"
        ]

    elif org_type == "nonprofit":
        return [
            "Funding Advisor (focus on donations)",
            "Community Impact Advisor (focus on outreach)",
            "Volunteer Advisor (focus on participation)",
            "Outreach Advisor (focus on awareness)",
            "Operations Advisor (focus on logistics)"
        ]

    elif org_type == "university":
        return [
            "Academic Advisor (focus on educational value)",
            "Budget Advisor (focus on cost efficiency)",
            "Student Engagement Advisor (focus on participation)",
            "Faculty Advisor (focus on academic goals)",
            "Scheduling Advisor (focus on feasibility)"
        ]



def agent_response(role, question, event_data, scores):

    # Role-based scoring bias
    role_scores = {}

    for event in event_data.index:

        cost = event_data.loc[event, "avg_cost"]
        attendance = event_data.loc[event, "avg_attendance"]
        satisfaction = event_data.loc[event, "member_satisfaction"]
        difficulty = event_data.loc[event, "organization_difficulty"]

        if "Finance" in role:
            score = attendance - cost * 0.5

        elif "Marketing" in role:
            score = attendance * 1.5 + satisfaction

        elif "Operations" in role:
            score = satisfaction - difficulty * 2

        elif "HR" in role:
            score = satisfaction * 2 - difficulty

        elif "Strategy" in role:
            score = attendance + satisfaction - cost * 0.2

        else:
            score = scores[event]

        role_scores[event] = score

    vote = max(role_scores, key=role_scores.get)

    explanation_prompt = f"""
    You are an advisor participating in a strategy decision.

    Your role:
    {role}

    User question:
    {question}

    Available options and data:
    {event_data}

    Calculated scores:
    {scores}

    IMPORTANT:
    You must vote ONLY for the option with the highest calculated score.

    Highest score option:
    {vote}

    Explain briefly why this option makes sense from your role perspective.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": explanation_prompt}],
            temperature=0.5,
            timeout=20
        )

        explanation = response.choices[0].message.content

    except:
        explanation = f"{role}: I recommend {vote} based on my priorities."

    return explanation + f"\n\nVOTE: {vote}"


def get_question_weights(question):

    question = question.lower()

    # default weights
    weights = {
        "attendance": 0.35,
        "satisfaction": 0.35,
        "cost": 0.2,
        "difficulty": 0.1
    }

    if "engagement" in question or "attendance" in question:
        weights["attendance"] += 0.15

    if "limited budget" in question or "low cost" in question or "cheap" in question:
        weights["cost"] += 0.15

    if "easy" in question or "feasible" in question:
        weights["difficulty"] += 0.15

    if "satisfaction" in question or "experience" in question:
        weights["satisfaction"] += 0.15

    # normalize
    total = sum(weights.values())
    for k in weights:
        weights[k] /= total

    return weights


def calculate_scores(event_data, question):

    weights = get_question_weights(question)

    scores = {}

    max_cost = event_data["avg_cost"].max()
    max_attendance = event_data["avg_attendance"].max()
    max_diff = event_data["organization_difficulty"].max()
    max_sat = event_data["member_satisfaction"].max()

    for event in event_data.index:

        cost = event_data.loc[event, "avg_cost"] / max_cost
        attendance = event_data.loc[event, "avg_attendance"] / max_attendance
        difficulty = event_data.loc[event, "organization_difficulty"] / max_diff
        satisfaction = event_data.loc[event, "member_satisfaction"] / max_sat

        score = (
            (attendance * weights["attendance"]) +
            (satisfaction * weights["satisfaction"]) -
            (cost * weights["cost"]) -
            (difficulty * weights["difficulty"])
        )

        scores[event] = round(score, 3)

    return scores

def debate_response(role, opinions):

    prompt = f"""
You are an advisor participating in a strategy meeting for a university student organization.

Your role:
{role}

These are the opinions from other advisors:

{opinions}

Briefly critique or challenge at least one other advisor's reasoning.
Explain if you disagree and why.

Keep your response short (2–3 sentences).
"""

    response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.5,
    timeout=20
)

    return response.choices[0].message.content


def generate_pdf_report(question, winner, confidence):

    styles = getSampleStyleSheet()

    file = SimpleDocTemplate("AI_strategy_report.pdf")

    content = []

    content.append(Paragraph("AI Strategy Advisory Report", styles['Title']))
    content.append(Spacer(1,20))

    content.append(Paragraph(f"Question: {question}", styles['Normal']))
    content.append(Spacer(1,20))

    content.append(Paragraph(f"Final Recommendation: {winner}", styles['Normal']))
    content.append(Spacer(1,20))

    content.append(Paragraph(f"Confidence Level: {confidence}%", styles['Normal']))

    file.build(content)

def risk_analysis(event_data):

    print("\nAI Risk Analysis")
    print("----------------")

    for event in event_data.index:

        cost = event_data.loc[event,"avg_cost"]
        difficulty = event_data.loc[event,"organization_difficulty"]

        if cost > 200 or difficulty >= 4:
            risk = "HIGH"
        elif cost > 120:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        print(f"{event} → {risk}")

def run_strategy_session(question):

        org_type = select_organization()
        event_data = load_event_data(org_type)
        agents = get_advisors(org_type)

        print("\nHistorical Event Data:\n")
        print(event_data)
        print("\n")


        results = []
        votes = {}
        scores = calculate_scores(event_data, question)

        print("\nCalculated Scores:\n", scores)
        print("\nDecision Insight:")

        best_option = max(scores, key=scores.get)

        print(f"Overall best option from data: {best_option}")

        print("But final decision may change based on question priorities.\n")
        print("\nAI Strategy Advisory Board\n")

        # Round 1 — Initial opinions
        for agent in agents:

            opinion = agent_response(agent, question, event_data, scores)

            print(agent)
            print(opinion)
            print("\n-----------------\n")

        

            results.append(opinion)

            vote_value = opinion.split("VOTE:")[-1].strip()
            votes[agent] = vote_value

        # Round 2 — Debate
        print("\nDEBATE ROUND\n")

        combined_opinions = "\n\n".join(results)

        for agent in agents:

            critique = debate_response(agent, combined_opinions)

            print(agent, "responds:")
            print(critique)
            print("\n-----------------\n")

            

        # Voting results
        print("\nAGENT VOTES\n")

        for agent, vote in votes.items():
            print(agent, "→", vote)

        vote_count = {}

        for vote in votes.values():
            vote_count[vote] = vote_count.get(vote, 0) + 1

        max_votes = max(vote_count.values())

        top_choices = [k for k,v in vote_count.items() if v == max_votes]

        if len(top_choices) > 1:
            # tie breaker using global scores
            winner = max(top_choices, key=lambda x: scores[x])
        else:
            winner = top_choices[0]

        confidence = (max_votes / len(votes)) * 100

        risk_analysis(event_data)

        labels = list(vote_count.keys())
        values = list(vote_count.values())

        plt.bar(labels, values)
        plt.title("AI Advisor Voting Results")
        plt.xlabel("Event Option")
        plt.ylabel("Number of Votes")

        plt.savefig("voting_results.png")
        plt.close()

        
       
       
        # Final recommendation
        final_prompt = f"""
        Combine the following advisor opinions and produce a final recommendation.

        Question:
        {question}

        Advisor opinions:
        {results}

        Vote summary:
        {votes}

        Top choice(s): {winner}
        Votes received: {max_votes} out of {len(votes)}

        Write a short strategic recommendation explaining the result.
        """

        final_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": final_prompt}
            ]
        )
        final_text = final_response.choices[0].message.content

        generate_pdf_report(question, winner, round(confidence,2))

        # Final results
        print("\n" + "="*50)
        print("FINAL AI STRATEGIC RECOMMENDATION")
        print("="*50)

        print(final_text)

        print("\nConfidence Level:", round(confidence, 2), "%")

        print("\nPDF report generated: AI_strategy_report.pdf")

        return {
            "votes": votes,
            "winner": winner,
            "confidence": round(confidence, 2),
            "recommendation": final_text,
            "data_summary": event_data.to_dict()
            } 
        


if __name__ == "__main__":
    question = input("\nType your strategy question and press Enter:\n> ")

    run_strategy_session(question)
