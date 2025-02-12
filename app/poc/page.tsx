"use client";
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Message {
  role: "user" | "assistant" | "system";
  type: "message" | "tool_use" | "tool_result";
  content?: string;
  tool?: string;
  id?: string;
  arguments?: any;
  result?: any;
}

const PocPage: React.FC = () => {
  // Initialize with the TP53 studies conversation (example 4) only
  const conversation: Message[] = [
    {
      role: "user",
      type: "message",
      content: "What are the latest studies on TP53 mutations in lung cancer?",
    },
    {
      role: "assistant",
      type: "tool_use",
      tool: "get_pubmed_studies",
      id: "toolu_01TP53StudyCall",
      arguments: {
        query: "TP53 mutations in lung cancer",
        sources: ["PubMed", "Genomic Repositories"],
      },
    },
    {
      role: "system",
      type: "tool_result",
      tool: "get_pubmed_studies",
      id: "toolu_01TP53StudyCall",
      result: {
        studies: [
          {
            title: "Impact of TP53 Mutations on Treatment Resistance",
            journal: "Lung Cancer",
            year: 2024,
            summary:
              "A detailed study exploring the role of TP53 mutations in lung cancer treatment outcomes.",
          },
          {
            title: "Prognostic Implications of TP53 Mutations: A Meta-analysis",
            journal: "Clinical Cancer Research",
            year: 2023,
            summary:
              "This meta-analysis discusses how TP53 mutations could serve as prognostic factors in lung cancer.",
          },
          {
            title: "Targeted Therapies for TP53 Mutated Lung Cancer",
            journal: "Ongoing Trials",
            year: "Ongoing",
            summary:
              "A review of current and incipient trials investigating targeted therapies.",
          },
        ],
      },
    },
    {
      role: "assistant",
      type: "message",
      content:
        "Based on the latest data aggregated from PubMed and several genomic repositories, recent studies on TP53 mutations in lung cancer reveal that inactivation of TP53 is strongly correlated with poor prognosis. Key research highlights include:\n\n- A 2024 study in _Lung Cancer_ journal, detailing the impact of TP53 mutations on treatment resistance.\n- A 2023 meta-analysis in _Clinical Cancer Research_ discussing the prognostic implications.\n- Ongoing trials investigating targeted therapies for patients with TP53 mutations.\n\nWould you like a list of these studies with abstracts, or do you prefer a more detailed analysis of one specific study?",
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="text-2xl font-bold">
              Natural Language Query Interface - Proof of Concept
            </CardTitle>
          </CardHeader>
          <CardContent>
            {conversation.map((msg, index) => {
              let displayText: React.ReactNode = "";
              switch (msg.type) {
                case "message":
                  displayText = msg.content || "";
                  break;
                case "tool_use":
                  if (msg.tool === "get_pubmed_studies") {
                    displayText = (
                      <div className="flex flex-col gap-1">
                        <span className="font-bold text-green-600">
                          PubMed Studies Call
                        </span>
                        <span className="text-sm text-gray-600">
                          Fetching studies for query:{" "}
                          <code>{msg.arguments.query}</code>
                        </span>
                        <span className="text-xs text-gray-500">
                          Sources:{" "}
                          {Array.isArray(msg.arguments.sources)
                            ? msg.arguments.sources.join(", ")
                            : msg.arguments.sources}
                        </span>
                      </div>
                    );
                  } else {
                    displayText = `Calling tool ${
                      msg.tool
                    } with arguments: ${JSON.stringify(msg.arguments)}`;
                  }
                  break;
                case "tool_result":
                  if (
                    msg.tool === "get_pubmed_studies" &&
                    msg.result &&
                    msg.result.studies
                  ) {
                    displayText = (
                      <div className="flex flex-col gap-3">
                        <span className="font-bold text-blue-600">
                          PubMed Studies:
                        </span>
                        {msg.result.studies.map((study: any, idx: number) => (
                          <div
                            key={idx}
                            className="border border-gray-300 rounded shadow-sm p-4"
                          >
                            <h4 className="font-bold text-lg text-blue-600">
                              {study.title}
                            </h4>
                            <p className="text-sm text-gray-600">
                              {study.journal} - {study.year}
                            </p>
                            <p className="mt-2 text-gray-700">
                              {study.summary}
                            </p>
                          </div>
                        ))}
                      </div>
                    );
                  } else {
                    displayText = (
                      <div className="flex flex-col gap-1">
                        <span className="font-bold text-blue-600">
                          Tool Result from {msg.tool}
                        </span>
                        <pre className="whitespace-pre-wrap break-words text-sm text-gray-700 bg-gray-100 p-2 rounded border border-gray-300 shadow-sm">
                          {JSON.stringify(msg.result, null, 2)}
                        </pre>
                      </div>
                    );
                  }
                  break;
                default:
                  displayText = "";
              }
              const alignClass =
                msg.role === "user" ? "justify-end" : "justify-start";
              const bgClass =
                msg.role === "user"
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 text-black";
              return (
                <div key={index} className={`flex ${alignClass} my-2`}>
                  <div className={`rounded-xl px-4 py-2 ${bgClass}`}>
                    {displayText}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PocPage;
