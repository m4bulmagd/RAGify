"use client"

import { DocumentUploader } from "@/components/documents/document-uploader"
import { DocumentList } from "@/components/documents/document-list"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function ProjectDocuments({ projectId }: { projectId: string }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
         <div>
            <h3 className="text-lg font-medium">Knowledge Base</h3>
            <p className="text-sm text-muted-foreground">Manage documents and embeddings.</p>
         </div>
      </div>

      <Tabs defaultValue="list" className="w-full">
        <TabsList>
          <TabsTrigger value="list">All Documents</TabsTrigger>
          <TabsTrigger value="upload">Upload</TabsTrigger>
        </TabsList>
        <TabsContent value="list" className="mt-6">
           {/* TODO: Pass projectId to DocumentList to filter */}
          <DocumentList />
        </TabsContent>
        <TabsContent value="upload" className="mt-6">
           {/* TODO: Pass projectId to DocumentUploader */}
          <DocumentUploader />
        </TabsContent>
      </Tabs>
    </div>
  )
}
