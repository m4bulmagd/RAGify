import { DocumentUploader } from "@/components/documents/document-uploader"
import { DocumentList } from "@/components/documents/document-list"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function DocumentsPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-bold tracking-tight glow-text">Documents</h2>
        <p className="text-muted-foreground mt-2">
          Upload and manage your knowledge base.
        </p>
      </div>

      <Tabs defaultValue="list" className="w-full">
        <TabsList>
          <TabsTrigger value="list">All Documents</TabsTrigger>
          <TabsTrigger value="upload">Upload</TabsTrigger>
        </TabsList>
        <TabsContent value="list" className="mt-6">
          <DocumentList />
        </TabsContent>
        <TabsContent value="upload" className="mt-6">
          <DocumentUploader />
        </TabsContent>
      </Tabs>
    </div>
  )
}
