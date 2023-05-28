# 🚀 Geniusrise-CLI

Welcome to Geniusrise-CLI, a powerful command-line tool that is part of the
Geniusrise project. This tool is designed to pull data from various sources,
format it, and create and manage fine-tuned Language Learning Models (LLMs).

## 📚 Structure

The `geniusrise-cli` tool is structured into several modules, each responsible
for a specific task:

- `main.py`: The main entry point for the tool.
- `bard.py`: Handles a specific LLM.
- `chatgpt.py`: Handles the ChatGPT LLM.
- `base.py`: Base module for the LLM.
- `cmdline.py`: Handles command line arguments and options.

## 🌐 Data Platforms

Geniusrise-CLI integrates with a wide range of data platforms across various
categories:

| Communication                    | Project Management            | Document Management                 | Code Hosting                      | Customer Support                  | CRM                                |
| -------------------------------- | ----------------------------- | ----------------------------------- | --------------------------------- | --------------------------------- | ---------------------------------- |
| Discord (Chat for communities)   | ClickUp (Task management)     | Dropbox (Cloud storage)             | GitLab (DevOps tool)              | Zendesk (Customer service)        | Zoho (Online office suite)         |
| Slack (Messaging platform)       | Jira (Issue tracking)         | Notion (Notes and databases)        | Static (Code hosting)             | Intercom (Customer communication) | HubSpot (Marketing and sales)      |
| Microsoft Teams (Workplace chat) | Asana (Work management)       | Google Drive (File storage)         | Bitbucket Server (Git repository) | Freshdesk (Customer support)      | Salesforce (Customer relationship) |
|                                  | Basecamp (Project management) | Confluence (Collaboration software) | GitHub (Developer platform)       |                                   |                                    |

## 🎯 Application of Fine-Tuned LLMs

Once the target LLM is trained, it can be used by various roles within an
organization to assist with their specific tasks. Here are some examples:

- **Product Managers**: Generate Product Requirement Documents (PRDs) using the
  LLM. For instance, the LLM can be used to draft the initial version of a PRD,
  which can then be refined by the product manager.

- **Developers**: Generate code snippets or pseudocode to help with development
  tasks. For example, a developer could input a high-level description of a
  function into the LLM, and the LLM could output a rough draft of the function
  in code.

- **Sales and Marketing**: Generate sales pitches, marketing material, or
  customer emails. For instance, a salesperson could use the LLM to generate a
  pitch for a new product, or a marketer could use it to draft a new blog post
  or social media update.

- **Support**: Generate responses to common customer inquiries. For example, a
  support agent could use the LLM to quickly draft responses to frequently asked
  questions.

- **Finance**: Generate invoices or financial reports. For instance, a finance
  team member could use the LLM to draft an invoice for a customer, or to
  generate a first draft of a financial report.

By fine-tuning the LLMs to your organization's specific needs, you can create a
powerful tool that assists with a wide range of tasks across your organization.

## 🔄 Preprocessing

The tool includes modules for preprocessing data:

- `prompts.py`: Handles prompts in preprocessing.
- `openai.py`: Preprocesses data for OpenAI.
- `google_palm.py`: Preprocesses data for Google PALM.

## 🎛️ Fine-Tuning Process

The fine-tuning process in Geniusrise-CLI involves pulling data from various
sources, piping them into various LLMs to generate prompts, and then using these
prompts to fine-tune the target model. Here's a PlantUML diagram to illustrate
the process:

```plantuml
@startuml
skinparam monochrome false
skinparam shadowing true
skinparam componentStyle uml2
skinparam component {
  BackgroundColor #E5E4E2
  BorderColor #333333
}
skinparam database {
  BackgroundColor #F4A460
  BorderColor #8B4513./assets/fine-tuning.png
}
skinparam arrow {
  Color #000000
}

title Fine-Tuning Process

database "Data Sources" as DS
actor "LLMs + RLHF" as LLM
database "Prompts" as P
component "Target LLM" as TM

DS --> LLM : Pull Data
LLM --> P : Generate Prompts
P --> TM : Fine-Tune Model
note right of TM
  Once fine-tuned, the LLM can be used by various roles within an organization:
  - Product Managers: Generate PRDs
  - Developers: Generate code snippets
  - Sales and Marketing: Generate sales pitches and marketing material
  - Support: Generate responses to customer inquiries
  - Finance: Generate invoices and financial reports
end note

@enduml

```

![ft](./assets/fine-tuning.png)

## 🚀 Getting Started

To get started with `geniusrise-cli`, clone the repository and install the
necessary dependencies.

## 🤝 Contributing

We welcome contributions to the `geniusrise-cli` tool. If you're interested in
contributing, please take a look at our open issues and submit a pull request
when you're ready.

## 📜 License

Geniusrise-CLI is open-source software licensed under [LICENSE].

## 📞 Contact

If you have any questions or suggestions, please feel free to reach out to us at
[CONTACT INFORMATION].

Join us on this exciting journey to create "geniuses"! 🎉
