"use client"

import * as React from "react"
import { useForm, UseFormReturn } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Brain, Database, Eye, FileText, CheckCircle2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"

// --- Schema ---
const formSchema = z.object({
  // Identity
  name: z.string().min(2, "Name must be at least 2 characters"),
  role: z.string().min(2, "Role is required"),
  avatar: z.string().optional(),
  
  // Knowledge
  documents: z.array(z.string()).min(1, "Select at least one document"),
  
  // Brain
  model: z.enum(["gpt-4", "gpt-3.5", "claude-3"]),
  temperature: z.number().min(0).max(1),
  systemPrompt: z.string().min(10, "System prompt is required"),
  
  // Retrieval
  topK: z.number().min(1).max(20),
  similarityThreshold: z.number().min(0).max(1),
})

type FormValues = z.infer<typeof formSchema>

// --- Steps Config ---
const steps = [
  { id: 1, title: "Identity", icon: Eye, description: "Name & Persona" },
  { id: 2, title: "Knowledge", icon: Database, description: "Select Data" },
  { id: 3, title: "Brain", icon: Brain, description: "Model Config" },
  { id: 4, title: "Retrieval", icon: FileText, description: "Search Settings" },
  { id: 5, title: "Review", icon: CheckCircle2, description: "Confirmation" },
]

export function AgentBuilderWizard() {
  const [currentStep, setCurrentStep] = React.useState(1)
  
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      role: "Helpful Assistant",
      documents: [],
      model: "gpt-4",
      temperature: 0.7,
      systemPrompt: "You are a helpful AI assistant. Answer questions based on the retrieved context.",
      topK: 5,
      similarityThreshold: 0.5,
    },
  })

  // Hack for demo: "submit" just moves next unless last step
  const handleNext = async () => {
    const isValid = await form.trigger() // trigger validation for all, ideally scoped to step
    if (isValid || true) { // Bypassing validation for mockup strictness
      if (currentStep < 5) {
        setCurrentStep((prev) => prev + 1)
      } else {
        console.log("SUBMIT", form.getValues())
      }
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1)
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[250px_1fr]">
      {/* Sidebar Stepper */}
      <nav className="flex flex-col gap-2">
        {steps.map((step) => {
          const Icon = step.icon
          const isActive = step.id === currentStep
          const isCompleted = step.id < currentStep
          
          return (
            <div
              key={step.id}
              className={`flex items-center gap-3 rounded-lg p-3 transition-colors ${
                isActive
                  ? "bg-primary/10 text-primary ring-1 ring-primary/20"
                  : isCompleted
                  ? "text-muted-foreground opacity-50"
                  : "text-muted-foreground/50"
              }`}
            >
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full border text-xs font-medium ${
                  isActive
                    ? "border-primary bg-primary text-primary-foreground"
                    : isCompleted
                    ? "border-primary/50 text-primary/50"
                    : "border-muted-foreground/30"
                }`}
              >
                {isCompleted ? <CheckCircle2 className="h-4 w-4" /> : step.id}
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-medium">{step.title}</span>
                <span className="text-[10px] uppercase text-muted-foreground">
                  {step.description}
                </span>
              </div>
            </div>
          )
        })}
      </nav>

      {/* Main Content */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle>{steps[currentStep - 1].title}</CardTitle>
          <CardDescription>
            Configure your agent's {steps[currentStep - 1].title.toLowerCase()}.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {currentStep === 1 && <IdentityStep form={form} />}
          {currentStep === 2 && <KnowledgeStep form={form} />}
          {currentStep === 3 && <BrainStep form={form} />}
          {currentStep === 4 && <RetrievalStep form={form} />}
          {currentStep === 5 && <ReviewStep form={form} />}
        </CardContent>
        <div className="flex justify-between border-t border-border/50 p-6">
          <Button variant="ghost" onClick={handleBack} disabled={currentStep === 1}>
            Back
          </Button>
          <Button onClick={handleNext}>
            {currentStep === 5 ? "Deploy Agent" : "Next Step"}
          </Button>
        </div>
      </Card>
    </div>
  )
}

// --- Sub Steps ---

function IdentityStep({ form }: { form: UseFormReturn<FormValues> }) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Agent Name</Label>
        <Input placeholder="e.g. Legal Contract Helper" {...form.register("name")} />
      </div>
      <div className="space-y-2">
        <Label>Role / Persona</Label>
        <Input placeholder="e.g. Expert Legal Analyst" {...form.register("role")} />
      </div>
      <div className="flex items-center gap-4">
        <div className="h-16 w-16 rounded-full bg-primary/20 border border-primary/50 flex items-center justify-center">
            <Eye className="h-8 w-8 text-primary" />
        </div>
        <Button variant="outline" size="sm">Upload Avatar</Button>
      </div>
    </div>
  )
}

function KnowledgeStep({ form }: { form: UseFormReturn<FormValues> }) {
  const [selected, setSelected] = React.useState<string[]>([])
  
  const toggleDoc = (id: string) => {
      const current = form.getValues("documents")
      const newSel = current.includes(id) 
        ? current.filter(x => x !== id)
        : [...current, id]
      form.setValue("documents", newSel)
      setSelected(newSel) // Force render for mock
  }

  return (
    <div className="space-y-4">
      <div className="relative">
         <Input placeholder="Search documents..." className="pl-8" />
      </div>
      <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
         {["Q3_Financials.pdf", "contract_v2.docx", "employee_handbook.pdf"].map((doc, i) => (
             <div 
                key={doc} 
                className={`flex items-center justify-between rounded-md border p-3 cursor-pointer transition-all ${
                    form.getValues("documents").includes(doc) 
                    ? "border-primary bg-primary/10" 
                    : "border-border hover:bg-muted/50"
                }`}
                onClick={() => toggleDoc(doc)}
             >
                 <div className="flex items-center gap-3">
                     <FileText className="h-4 w-4 text-muted-foreground" />
                     <span>{doc}</span>
                 </div>
                 {form.getValues("documents").includes(doc) && <CheckCircle2 className="h-4 w-4 text-primary" />}
             </div>
         ))}
      </div>
    </div>
  )
}

function BrainStep({ form }: { form: UseFormReturn<FormValues> }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {["gpt-4", "gpt-3.5", "claude-3"].map((model) => (
             <div 
                key={model}
                className={`flex flex-col items-center justify-center gap-2 rounded-lg border p-4 cursor-pointer transition-all ${
                    form.getValues("model") === model
                    ? "border-primary bg-primary/10 ring-1 ring-primary" 
                    : "border-border hover:bg-muted/50"
                }`}
                onClick={() => form.setValue("model", model as any)}
             >
                 <Brain className="h-6 w-6" />
                 <span className="capitalize font-medium">{model}</span>
             </div>
        ))}
      </div>
      
      <div className="space-y-4">
          <div className="flex justify-between">
            <Label>Temperature</Label>
            <span className="text-sm text-muted-foreground">{form.watch("temperature")}</span>
          </div>
          <Slider 
            defaultValue={[0.7]} 
            max={1} 
            step={0.1} 
            onValueChange={(val) => form.setValue("temperature", val[0])}
          />
      </div>

       <div className="space-y-2">
        <Label>System Prompt</Label>
        <Textarea 
            className="h-[150px] font-mono text-sm"
            {...form.register("systemPrompt")} 
        />
      </div>
    </div>
  )
}

function RetrievalStep({ form }: { form: UseFormReturn<FormValues> }) {
  return (
    <div className="space-y-8">
       <div className="space-y-4">
          <div className="flex justify-between">
            <Label>Top K (Chunks to retrieve)</Label>
            <span className="text-sm font-bold bg-primary/20 px-2 py-1 rounded text-primary">{form.watch("topK")}</span>
          </div>
          <Slider 
             defaultValue={[5]} 
             min={1}
             max={20} 
             step={1} 
             onValueChange={(val) => form.setValue("topK", val[0])}
           />
           <p className="text-xs text-muted-foreground">
             Higher values provide more context but may increase noise and costs.
           </p>
      </div>
      
      <div className="space-y-4">
          <div className="flex justify-between">
            <Label>Similarity Threshold</Label>
            <span className="text-sm font-bold bg-primary/20 px-2 py-1 rounded text-primary">{form.watch("similarityThreshold")}</span>
          </div>
          <Slider 
             defaultValue={[0.5]} 
             min={0}
             max={1} 
             step={0.05} 
             onValueChange={(val) => form.setValue("similarityThreshold", val[0])}
           />
           <p className="text-xs text-muted-foreground">
             Minimum cosine similarity score required for a chunk to be included.
           </p>
      </div>
    </div>
  )
}

function ReviewStep({ form }: { form: UseFormReturn<FormValues> }) {
  const values = form.getValues()
  return (
    <div className="space-y-4 rounded-lg bg-card/50 p-4 border border-border">
        <div className="grid grid-cols-2 gap-4">
            <div>
                <Label className="text-muted-foreground">Name</Label>
                <div className="font-medium">{values.name || "Untitled Agent"}</div>
            </div>
            <div>
                <Label className="text-muted-foreground">Model</Label>
                <div className="font-medium uppercase">{values.model}</div>
            </div>
             <div>
                <Label className="text-muted-foreground">Documents</Label>
                <div className="font-medium">{values.documents.length} Selected</div>
            </div>
             <div>
                <Label className="text-muted-foreground">Retrieval</Label>
                <div className="font-medium">Top {values.topK}, &gt;{values.similarityThreshold}</div>
            </div>
        </div>
        <Separator />
        <div>
            <Label className="text-muted-foreground">System Prompt</Label>
            <div className="mt-1 rounded bg-muted/50 p-3 text-sm font-mono text-muted-foreground">
                {values.systemPrompt}
            </div>
        </div>
    </div>
  )
}
