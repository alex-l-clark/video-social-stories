import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Sparkles, Clock, Download, CheckCircle, AlertCircle, RefreshCw, FileVideo, Timer } from "lucide-react";
import { toast } from "@/hooks/use-toast";
interface SocialStoryData {
  situation: string;
  setting: string;
  age?: number;
  reading_level?: string;
  diagnosis_summary?: string;
}
interface JobStatus {
  job_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  error?: string;
}
const READING_LEVELS = [{
  value: "early_reader",
  label: "Early Reader (K-2)"
}, {
  value: "developing_reader",
  label: "Developing Reader (3-5)"
}, {
  value: "intermediate_reader",
  label: "Intermediate Reader (6-8)"
}, {
  value: "advanced_reader",
  label: "Advanced Reader (9+)"
}];
export default function SocialStoryForm() {
  const [formData, setFormData] = useState<SocialStoryData>({
    situation: "",
    setting: ""
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<number>(0);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://api.example.com";
  const handleInputChange = (field: keyof SocialStoryData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };
  const pollJobStatus = async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/jobs/${jobId}`);
      const data = await response.json();
      setJobStatus(data);
      if (data.status === "succeeded") {
        toast({
          title: "Video Ready!",
          description: "Your social story video is ready for download."
        });
        return true;
      } else if (data.status === "failed") {
        toast({
          title: "Generation Failed",
          description: data.error || "Failed to generate video",
          variant: "destructive"
        });
        setIsGenerating(false);
        return true;
      }
      return false;
    } catch (error) {
      console.error("Error polling job status:", error);
      toast({
        title: "Connection Error",
        description: "Error checking video status. Please try again.",
        variant: "destructive"
      });
      setIsGenerating(false);
      return true;
    }
  };
  const startPolling = async (jobId: string) => {
    let attempts = 0;
    const maxAttempts = 150; // 5 minutes with 2-second intervals
    const startTime = Date.now();
    setEstimatedTime(120); // 2 minutes estimated

    // Timer to update elapsed time
    const timer = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      const isComplete = await pollJobStatus(jobId);
      if (isComplete) {
        clearInterval(timer);
        break;
      }
      attempts++;
    }
    if (attempts >= maxAttempts) {
      clearInterval(timer);
      toast({
        title: "Generation Timeout",
        description: "Video generation is taking longer than expected. Please try again.",
        variant: "destructive"
      });
      setIsGenerating(false);
    }
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.situation.trim() || !formData.setting.trim()) {
      toast({
        title: "Missing Information",
        description: "Please fill in both situation and setting fields",
        variant: "destructive"
      });
      return;
    }
    setIsGenerating(true);
    setJobStatus(null);
    setDownloadUrl(null);
    setElapsedTime(0);
    setEstimatedTime(0);
    try {
      const payload = {
        ...formData,
        age: formData.age || undefined
      };
      const response = await fetch(`${API_BASE_URL}/v1/social-story:start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        throw new Error("Failed to start video generation");
      }
      const {
        job_id
      } = await response.json();
      toast({
        title: "Generation Started",
        description: "Your social story video is being created. This usually takes 2-3 minutes."
      });
      setJobStatus({
        job_id,
        status: "queued"
      });
      await startPolling(job_id);
    } catch (error) {
      console.error("Error starting job:", error);
      toast({
        title: "Generation Failed",
        description: "Failed to start video generation. Please check your connection and try again.",
        variant: "destructive"
      });
      setIsGenerating(false);
    }
  };
  const handleDownload = async () => {
    if (!jobStatus?.job_id) return;
    try {
      const response = await fetch(`${API_BASE_URL}/v1/jobs/${jobStatus.job_id}/download`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `social-story-${jobStatus.job_id}.mp4`;
      a.click();
      URL.revokeObjectURL(url);
      toast({
        title: "Download Complete",
        description: "Your social story video has been downloaded successfully!"
      });

      // Reset form after successful download
      setFormData({
        situation: "",
        setting: ""
      });
      setJobStatus(null);
      setIsGenerating(false);
    } catch (error) {
      console.error("Error downloading video:", error);
      toast({
        title: "Download Failed",
        description: "Failed to download video. Please try again.",
        variant: "destructive"
      });
    }
  };
  const handleRetry = () => {
    setJobStatus(null);
    setIsGenerating(false);
    setElapsedTime(0);
    setEstimatedTime(0);
  };
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  const getStatusIcon = () => {
    if (!jobStatus) return null;
    switch (jobStatus.status) {
      case "queued":
        return <Timer className="w-5 h-5 text-primary animate-pulse" />;
      case "running":
        return <RefreshCw className="w-5 h-5 text-primary animate-spin" />;
      case "succeeded":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "failed":
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return null;
    }
  };
  const getStatusContent = () => {
    if (!jobStatus) return null;
    switch (jobStatus.status) {
      case "queued":
        return <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Timer className="w-5 h-5 text-primary animate-pulse" />
                <div>
                  <p className="font-medium text-primary">Your video is in the queue</p>
                  <p className="text-sm text-muted-foreground">
                    Estimated time: {estimatedTime > 0 ? `${Math.ceil(estimatedTime / 60)} minutes` : 'Calculating...'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium">{formatTime(elapsedTime)}</p>
                <p className="text-xs text-muted-foreground">elapsed</p>
              </div>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div className="bg-primary h-2 rounded-full w-1/4 animate-pulse"></div>
            </div>
            <p className="text-xs text-muted-foreground">
              Please keep this page open while your video is being created.
            </p>
          </div>;
      case "running":
        return <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <RefreshCw className="w-5 h-5 text-primary animate-spin" />
                <div>
                  <p className="font-medium text-primary">Creating your video story</p>
                  <p className="text-sm text-muted-foreground">
                    AI is generating scenes and narration...
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium">{formatTime(elapsedTime)}</p>
                <p className="text-xs text-muted-foreground">elapsed</p>
              </div>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div className="bg-primary h-2 rounded-full w-3/4 animate-pulse"></div>
            </div>
            <p className="text-xs text-muted-foreground">
              Please keep this page open while your video is being created.
            </p>
          </div>;
      case "succeeded":
        return <div className="space-y-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <div>
                <p className="font-medium text-green-700">Video ready for download!</p>
                <p className="text-sm text-muted-foreground">
                  Generation completed in {formatTime(elapsedTime)}
                </p>
              </div>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-amber-800">Important:</p>
                  <p className="text-amber-700">
                    This download link will expire when you leave or refresh this page. 
                    Please download your video now.
                  </p>
                </div>
              </div>
            </div>
            <Button onClick={handleDownload} className="w-full bg-green-600 hover:bg-green-700 shadow-soft">
              <Download className="w-4 h-4 mr-2" />
              Download Your Social Story Video
            </Button>
          </div>;
      case "failed":
        return <div className="space-y-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-red-600" />
              <div>
                <p className="font-medium text-red-700">Generation failed</p>
                <p className="text-sm text-muted-foreground">
                  {jobStatus.error || "An unexpected error occurred during video creation"}
                </p>
              </div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="text-sm text-red-700">
                <p className="font-medium mb-1">What you can try:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Check your internet connection</li>
                  <li>Simplify the situation description</li>
                  <li>Try again in a few minutes</li>
                  <li>Contact support if the problem persists</li>
                </ul>
              </div>
            </div>
            <Button onClick={handleRetry} variant="outline" className="w-full">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>;
      default:
        return null;
    }
  };
  return <div className="max-w-4xl mx-auto space-y-12 px-4">
      {/* Header - visible on desktop, hidden on mobile */}
      <div className="text-center space-y-6 hidden lg:block">
        <div className="flex items-center justify-center gap-3 mb-6">
          <BookOpen className="w-10 h-10 text-primary" />
          <h1 className="text-4xl font-bold bg-gradient-hero bg-clip-text text-transparent">
            Social Story Creator
          </h1>
        </div>
        <div className="max-w-2xl mx-auto space-y-4">
          <p className="text-muted-foreground text-xl">
            Brings social stories to life for more engaging lessons with students
          </p>
          <div className="bg-muted/30 rounded-lg p-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-2 justify-center">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>We do not store any information to protect student privacy</span>
            </div>
          </div>
        </div>
      </div>

      <Card className="shadow-card">
        <CardHeader className="space-y-2">
          {/* Mobile header - only visible on mobile */}
          <div className="lg:hidden text-center space-y-4 mb-6">
            <div className="flex items-center justify-center gap-3">
              <BookOpen className="w-8 h-8 text-primary" />
              <h1 className="text-3xl font-bold bg-gradient-hero bg-clip-text text-transparent">
                Social Story Creator
              </h1>
            </div>
            <p className="text-muted-foreground">
              Brings social stories to life for more engaging lessons with students
            </p>
            <div className="bg-muted/30 rounded-lg p-3 text-sm text-muted-foreground">
              <div className="flex items-center gap-2 justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>We do not store any information to protect student privacy</span>
              </div>
            </div>
          </div>
          
          <CardTitle className="flex items-center gap-2 text-2xl">
            <Sparkles className="w-6 h-6 text-primary" />
            Story Details
          </CardTitle>
          <CardDescription className="text-base">
            Provide the context and setting for your social story
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Situation - Full Width */}
            <div className="space-y-3">
              <Label htmlFor="situation" className="flex items-center gap-2 text-base font-medium">
                Situation <Badge variant="secondary" className="text-xs">Required</Badge>
              </Label>
              <p className="text-sm text-muted-foreground">Describe the specific behavior or situation you want to address</p>
              <Textarea id="situation" placeholder="Describe situation" value={formData.situation} onChange={e => handleInputChange("situation", e.target.value)} className="min-h-[120px] resize-none text-base" required />
            </div>

            {/* Setting - Full Width */}
            <div className="space-y-3">
              <Label htmlFor="setting" className="flex items-center gap-2 text-base font-medium">
                Setting <Badge variant="secondary" className="text-xs">Required</Badge>
              </Label>
              <p className="text-sm text-muted-foreground">Describe where this typically happens</p>
              <Textarea id="setting" placeholder="Describe setting" value={formData.setting} onChange={e => handleInputChange("setting", e.target.value)} className="min-h-[120px] resize-none text-base" required />
            </div>

            {/* Age and Reading Level - Side by Side */}
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-3">
                <Label htmlFor="age" className="text-base font-medium">Student Age</Label>
                <Select value={formData.age?.toString() || ""} onValueChange={value => handleInputChange("age", value ? parseInt(value) : undefined)}>
                  <SelectTrigger className="h-12 text-base">
                    <SelectValue placeholder="Select age" />
                  </SelectTrigger>
                  <SelectContent>
                    {Array.from({
                    length: 23
                  }, (_, i) => <SelectItem key={i} value={i.toString()}>
                        {i} years old
                      </SelectItem>)}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-3">
                <Label htmlFor="reading_level" className="text-base font-medium">Reading Level</Label>
                <Select value={formData.reading_level || ""} onValueChange={value => handleInputChange("reading_level", value || undefined)}>
                  <SelectTrigger className="h-12 text-base">
                    <SelectValue placeholder="Select reading level" />
                  </SelectTrigger>
                  <SelectContent>
                    {READING_LEVELS.map(level => <SelectItem key={level.value} value={level.value}>
                        {level.label}
                      </SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Diagnosis Notes - Full Width */}
            <div className="space-y-3">
              <Label htmlFor="diagnosis" className="text-base font-medium">Diagnosis Notes</Label>
              <p className="text-sm text-muted-foreground">Any relevant diagnosis information or behavioral notes</p>
              <Textarea id="diagnosis" placeholder="Add notes" value={formData.diagnosis_summary || ""} onChange={e => handleInputChange("diagnosis_summary", e.target.value || undefined)} className="min-h-[100px] resize-none text-base" />
            </div>

            {jobStatus && <Card className={`border-2 ${jobStatus.status === 'succeeded' ? 'border-green-200 bg-green-50' : jobStatus.status === 'failed' ? 'border-red-200 bg-red-50' : 'border-primary/20 bg-primary/5'}`}>
                <CardContent className="pt-6">
                  {getStatusContent()}
                </CardContent>
              </Card>}

            <Button type="submit" disabled={isGenerating || !formData.situation.trim() || !formData.setting.trim()} className="w-full bg-gradient-hero hover:shadow-glow transition-all duration-300 text-lg py-6" size="lg">
              {isGenerating ? <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Creating Video...
                </> : <>
                  <FileVideo className="w-4 h-4 mr-2" />
                  Generate Social Story
                </>}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>;
}