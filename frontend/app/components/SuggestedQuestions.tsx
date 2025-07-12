import { useThreadRuntime } from "@assistant-ui/react";
import { Card, CardTitle } from "./ui/card";
import { MapPin, Calendar, Users, Sparkles } from "lucide-react";

const suggestedQuestions = [
  {
    question: "How do I use a RecursiveUrlLoader to load content from a page?",
    icon: <Sparkles className="w-5 h-5" />,
    category: "Development"
  },
  {
    question: "How can I define the state schema for my LangGraph graph?",
    icon: <MapPin className="w-5 h-5" />,
    category: "Architecture"
  },
  {
    question: "How can I run a model locally on my laptop with Ollama?",
    icon: <Users className="w-5 h-5" />,
    category: "Setup"
  },
  {
    question: "Explain RAG techniques and how LangGraph can implement them.",
    icon: <Calendar className="w-5 h-5" />,
    category: "Concepts"
  },
];

export function SuggestedQuestions() {
  const threadRuntime = useThreadRuntime();

  const handleSend = (text: string) => {
    threadRuntime.append({
      role: "user",
      content: [{ type: "text", text }],
    });
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="mb-6 text-center">
        <h2 className="text-2xl font-semibold mb-2 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          Popular Questions
        </h2>
        <p className="text-muted-foreground">
          Get started with these commonly asked questions
        </p>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {suggestedQuestions.map((item, idx) => (
          <Card
            onClick={() => handleSend(item.question)}
            key={`suggested-question-${idx}`}
            className="group relative overflow-hidden cursor-pointer transition-all duration-300 ease-in-out hover:scale-[1.02] hover:shadow-lg border-2 border-transparent hover:border-primary/20 bg-card/80 backdrop-blur-sm"
          >
            {/* Gradient overlay on hover */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-accent/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            <div className="relative p-6">
              <div className="flex items-start gap-3 mb-3">
                <div className="flex-shrink-0 p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors duration-200">
                  {item.icon}
                </div>
                <div className="flex-1">
                  <div className="text-xs font-medium text-primary/70 uppercase tracking-wider mb-1">
                    {item.category}
                  </div>
                  <CardTitle className="text-foreground font-medium text-sm leading-6 group-hover:text-primary transition-colors duration-200">
                    {item.question}
                  </CardTitle>
                </div>
              </div>
              
              {/* Hover indicator */}
              <div className="absolute bottom-0 left-0 h-1 w-0 bg-gradient-to-r from-primary to-accent group-hover:w-full transition-all duration-300 ease-out" />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
