"""
Generate follow-up question suggestions for a chat answer.
"""

from langchain_core.prompts import PromptTemplate
from src.rag.graph_builder import llm

suggestion_prompt = PromptTemplate(
    template="""You are helping a user explore a document through a chatbot.

The user asked: {question}

The chatbot answered: {answer}

Write exactly 3 short follow-up questions the user might ask next.
Rules:
- Each question must be about the topic of the answer above.
- Keep each question under 12 words.
- Write one question per line, with no numbering and no extra text.

Follow-up questions:""",
    input_variables=["question", "answer"],
)


def get_followup_questions(question: str, answer: str) -> list:
    """
    Ask the LLM for 3 follow-up questions.

    Args:
        question: The question the user just asked.
        answer: The answer the chatbot gave.

    Returns:
        A list of up to 3 question strings (empty list if anything fails).
    """
    try:
        chain = suggestion_prompt | llm
        reply = chain.invoke({"question": question, "answer": answer})

        suggestions = []
        for line in reply.content.strip().split("\n"):
            line = line.strip().lstrip("-•*").strip()
            if line.endswith("?"):
                suggestions.append(line)

        return suggestions[:3]
    except Exception as e:
        print("Could not generate suggestions:", e)
        return []
    


































































































    