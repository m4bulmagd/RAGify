"use client"

import * as React from "react"
import { useForm, UseFormReturn } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Brain, Database, Eye, FileText, CheckCircle2, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

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
import { Badge } from "@/components/ui/badge"
import { useDocuments } from "@/hooks/use-documents"
import { Separator } from "@/components/ui/separator"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { apiFetch } from "@/lib/api"

// --- Schema ---
const formSchema = z.object({
  // Identity
  name: z.string().min(2, "Name must be at least 2 characters"),
  role: z.string().min(2, "Role is required"),
  description: z.string().optional(),
  
  // Knowledge
  document_ids: z.array(z.string()).min(1, "Select at least one document"),
  
  // Brain
  model: z.string().min(1, "Model is required"),
  provider: z.string().min(1, "Provider is required"),
  temperature: z.number().min(0).max(2),
  systemPrompt: z.string().min(10, "System prompt is required"),
  
  // Retrieval
  topK: z.number().min(1).max(20),
  similarityThreshold: z.number().min(0).max(1),
  retrievalMode: z.enum(["hybrid", "vector", "keyword"]),
  enableReranking: z.boolean().default(false),
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

interface AgentBuilderWizardProps {
    projectId: string
}

interface Provider {
    provider: string
    name: string
    models: {
        id: string
        name: string
        description: string
    }[]
}

export function AgentBuilderWizard({ projectId }: AgentBuilderWizardProps) {
  const [currentStep, setCurrentStep] = React.useState(1)
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [providers, setProviders] = React.useState<Provider[]>([])
  
  // ... form setup ...
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      role: "Helpful Assistant",
      description: "",
      document_ids: [],
      model: "gpt-4-turbo-preview", // Default, will change if dynamic
      provider: "openai",
      temperature: 0.7,
      systemPrompt: "You are a helpful AI assistant. Answer questions based on the retrieved context.",
      topK: 5,
      similarityThreshold: 0.5,
      retrievalMode: "hybrid",
      enableReranking: false,
    },
  })

  // Fetch providers
  React.useEffect(() => {
      const fetchProviders = async () => {
          try {
              const res = await apiFetch("/agents/providers")
              if(res.ok) {
                  const data = await res.json()
                  setProviders(data)
              }
          } catch (e) {
              console.error("Failed to fetch providers", e)
          }
      }
      fetchProviders()
  }, [])

  const { documents, isLoading: isLoadingDocs } = useDocuments(projectId)
  // ... rest of component ...

  const handleSubmit = async (values: FormValues) => {
      setIsSubmitting(true)
      try {
          // Transform for API
          const payload = {
              name: values.name,
              description: values.description || values.role, // role implies desc
              agent_type: "question-answering", // default
              project_id: projectId,
              document_ids: values.document_ids,
              llm_config: {
                  provider: values.provider,
                  model_name: values.model,
                  temperature: values.temperature,
                  system_prompt: values.systemPrompt,
                  enable_streaming: true
              },
              retrieval_config: {
                  retrieval_mode: values.retrievalMode,
                  top_k: values.topK,
                  similarity_threshold: values.similarityThreshold,
                  enable_reranking: values.enableReranking
              }
          }

          const res = await apiFetch("/agents/", {
              method: "POST",
              body: JSON.stringify(payload)
          })

          if (!res.ok) throw new Error("Failed to create agent")
          
          toast.success("Agent created successfully!")
          router.push(`/projects/${projectId}/agents`)
          
      } catch (error) {
          console.error(error)
          toast.error("Failed to create agent")
      } finally {
          setIsSubmitting(false)
      }
  }

  const handleNext = async () => {
    // Validate current step fields before moving
    let fieldsToValidate: any[] = []
    if (currentStep === 1) fieldsToValidate = ["name", "role", "description"]
    if (currentStep === 2) fieldsToValidate = ["document_ids"]
    if (currentStep === 3) fieldsToValidate = ["model", "provider", "temperature", "systemPrompt"]
    if (currentStep === 4) fieldsToValidate = ["topK", "similarityThreshold", "retrievalMode"]
    
    const isValid = await form.trigger(fieldsToValidate)
    
    if (isValid) {
      if (currentStep < 5) {
        setCurrentStep((prev) => prev + 1)
      } else {
        handleSubmit(form.getValues())
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
      <Card>
        <CardHeader>
          <CardTitle>{steps[currentStep - 1].title}</CardTitle>
          <CardDescription>
            Configure your agent's {steps[currentStep - 1].title.toLowerCase()}.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {currentStep === 1 && <IdentityStep form={form} />}
          {currentStep === 2 && <KnowledgeStep form={form} documents={documents || []} isLoading={isLoadingDocs} />}
          {currentStep === 3 && <BrainStep form={form} providers={providers} />}
          {currentStep === 4 && <RetrievalStep form={form} />}
          {currentStep === 5 && <ReviewStep form={form} documents={documents || []} />}
        </CardContent>
        <div className="flex justify-between border-t border-border/50 p-6">
          <Button variant="ghost" onClick={handleBack} disabled={currentStep === 1}>
            Back
          </Button>
          <Button onClick={handleNext} disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
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
        {form.formState.errors.name && <span className="text-sm text-destructive">{form.formState.errors.name.message}</span>}
      </div>
      <div className="space-y-2">
        <Label>Role / Persona</Label>
        <Input placeholder="e.g. Expert Legal Analyst" {...form.register("role")} />
        {form.formState.errors.role && <span className="text-sm text-destructive">{form.formState.errors.role.message}</span>}
      </div>
      <div className="space-y-2">
        <Label>Description</Label>
        <Textarea placeholder="Short description of what this agent does..." {...form.register("description")} />
      </div>
    </div>
  )
}

function KnowledgeStep({ form, documents, isLoading }: { form: UseFormReturn<FormValues>, documents: any[], isLoading: boolean }) {
  
  React.useEffect(() => {
     // If we have documents and none selected, maybe select all? Or none?
     // Default none is fine.
  }, [documents])

  const toggleDoc = (id: string) => {
      const current = form.getValues("document_ids")
      const newSel = current.includes(id) 
        ? current.filter(x => x !== id)
        : [...current, id]
      form.setValue("document_ids", newSel, { shouldValidate: true })
      // force update if needed (rhf sometimes needs proper registration)
  }

  if (isLoading) return <div className="p-4 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto"/> Loading documents...</div>

  return (
    <div className="space-y-4">
      <div className="relative">
         <Input placeholder="Search documents..." className="pl-8" />
         {/* Search logic unimplemented for now */}
      </div>
      <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
         {(!documents || documents.length === 0) && (
             <div className="text-center py-8 text-muted-foreground border border-dashed rounded-lg">
                 No documents found in this project.
             </div>
         )}
         {documents?.map((doc: any) => (
             <div 
                key={doc.id} 
                className={`flex items-center justify-between rounded-md border p-3 cursor-pointer transition-all ${
                    form.watch("document_ids").includes(doc.id) 
                    ? "border-primary bg-primary/10" 
                    : "border-border hover:bg-muted/50"
                }`}
                onClick={() => toggleDoc(doc.id)}
             >
                 <div className="flex items-center gap-3">
                     <FileText className="h-4 w-4 text-muted-foreground" />
                     <div className="flex flex-col">
                        <span className="text-sm font-medium">{doc.filename}</span>
                        <span className="text-xs text-muted-foreground">{(doc.size / 1024).toFixed(1)} KB</span>
                     </div>
                 </div>
                 {form.watch("document_ids").includes(doc.id) && <CheckCircle2 className="h-4 w-4 text-primary" />}
             </div>
         ))}
      </div>
      {form.formState.errors.document_ids && <span className="text-sm text-destructive">{form.formState.errors.document_ids.message}</span>}
    </div>
  )
}

function BrainStep({ form, providers }: { form: UseFormReturn<FormValues>, providers: Provider[] }) {
    const setModel = (model: string, provider: string) => {
        form.setValue("model", model as any)
        form.setValue("provider", provider as any)
    }
  
  return (
    <div className="space-y-6">
      <div className="space-y-4">
          <Label>Model</Label>
          <Select 
            value={form.watch("model")} 
            onValueChange={(value: string) => {
                // Find provider
                let provider = "openai"
                for(const p of providers) {
                    if(p.models.find(m => m.id === value)) {
                        provider = p.provider
                        break
                    }
                }
                setModel(value, provider)
            }}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select a model" />
            </SelectTrigger>
            <SelectContent>
              {providers.map(p => (
                   <SelectGroup key={p.provider}>
                       <SelectLabel>{p.name}</SelectLabel>
                       {p.models.map(m => (
                           <SelectItem key={m.id} value={m.id}>
                               {m.name}
                           </SelectItem>
                       ))}
                   </SelectGroup>
              ))}
            </SelectContent>
          </Select>
          {form.watch("model") && (
              <div className="text-sm text-muted-foreground p-2 bg-muted/50 rounded-md">
                 {/* Helper to show description */}
                 {providers.flatMap(p => p.models).find(m => m.id === form.watch("model"))?.description}
              </div>
          )}
      </div>
      
      <div className="space-y-4">
          <div className="flex justify-between">
            <Label>Temperature</Label>
            <span className="text-sm text-muted-foreground">{form.watch("temperature")}</span>
          </div>
          <Slider 
            defaultValue={[0.7]} 
            max={2} 
            step={0.1} 
            onValueChange={(val) => form.setValue("temperature", val[0])}
            value={[form.watch("temperature")]}
          />
      </div>

       <div className="space-y-2">
        <Label>System Prompt</Label>
        <Textarea 
            className="h-[150px] font-mono text-sm"
            {...form.register("systemPrompt")} 
        />
        {form.formState.errors.systemPrompt && <span className="text-sm text-destructive">{form.formState.errors.systemPrompt.message}</span>}
      </div>
    </div>
  )
}

import { Switch } from "@/components/ui/switch"

function RetrievalStep({ form }: { form: UseFormReturn<FormValues> }) {
  return (
    <div className="space-y-8">
       <div className="space-y-4">
          <div className="flex justify-between">
            <Label>Retrieval Mode</Label>
          </div>
          <Select 
            value={form.watch("retrievalMode")} 
            onValueChange={(val: any) => form.setValue("retrievalMode", val)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select mode" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="vector">Vector Only (Fast)</SelectItem>
              <SelectItem value="keyword">Keyword Only (Exact Match)</SelectItem>
              <SelectItem value="hybrid">Hybrid (Best of Both)</SelectItem>
            </SelectContent>
          </Select>
      </div>

       <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="space-y-0.5">
                <Label>Reranking (Cross-Encoder)</Label>
                <p className="text-xs text-muted-foreground">Significantly improves accuracy but slower.</p>
            </div>
            <Switch 
                checked={form.watch("enableReranking")}
                onCheckedChange={(checked) => form.setValue("enableReranking", checked)}
            />
          </div>
      </div>

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
             value={[form.watch("topK")]}
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
             value={[form.watch("similarityThreshold")]}
           />
           <p className="text-xs text-muted-foreground">
             Minimum cosine similarity score required for a chunk to be included.
           </p>
      </div>
    </div>
  )
}

function ReviewStep({ form, documents }: { form: UseFormReturn<FormValues>, documents: any[] }) {
  const values = form.getValues()
  const selectedDocs = documents?.filter(d => values.document_ids.includes(d.id)) || []

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
                <div className="font-medium">{selectedDocs.length} Selected</div>
                <div className="text-xs text-muted-foreground mt-1 max-h-15 overflow-y-auto">
                    {selectedDocs.map(d => d.filename).join(", ")}
                </div>
            </div>
             <div>
                <Label className="text-muted-foreground">Retrieval</Label>
                <div className="font-medium">Top {values.topK}, &gt;{values.similarityThreshold}</div>
            </div>
        </div>
        <Separator />
        <div>
            <Label className="text-muted-foreground">System Prompt</Label>
            <div className="mt-1 rounded bg-muted/50 p-3 text-sm font-mono text-muted-foreground max-h-25 overflow-y-auto">
                {values.systemPrompt}
            </div>
        </div>
    </div>
  )
}
