import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Sparkles, Clock, Download, CheckCircle, AlertCircle, RefreshCw, FileVideo, Timer, Smartphone, Wifi } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { downloadVideoWithRetry, getDeviceCapabilities, type DownloadResult } from "@/lib/downloadUtils";
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
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadResult, setDownloadResult] = useState<DownloadResult | null>(null);
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://api.example.com";
  
  // Get device capabilities for mobile optimization
  const deviceCapabilities = getDeviceCapabilities();
  const handleInputChange = (field: keyof SocialStoryData, value: string | number | undefined) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
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
    setElapsedTime(0);
    
    try {
      const payload = {
        ...formData,
        age: formData.age || undefined
      };
      
      toast({
        title: "Generation Started",
        description: "Creating your social story video... This usually takes 2-3 minutes."
      });
      
      // Show running status immediately
      setJobStatus({
        job_id: "generating",
        status: "running"
      });
      
      // Start timer for user feedback
      const startTime = Date.now();
      const timer = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
      
      // Backend runs synchronously and returns final result
      const response = await fetch(`${API_BASE_URL}/v1/social-story:start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      
      clearInterval(timer);
      
      if (!response.ok) {
        throw new Error("Failed to start video generation");
      }
      
      const result = await response.json();
      
      // Backend returns final status immediately
      setJobStatus({
        job_id: result.job_id,
        status: result.status,
        error: result.error
      });
      
      if (result.status === "succeeded") {
        toast({
          title: "Video Ready!",
          description: "Your social story video is ready for download."
        });
      } else if (result.status === "failed") {
        toast({
          title: "Generation Failed",
          description: result.error || "Failed to generate video",
          variant: "destructive"
        });
      }
      
      setIsGenerating(false);
      
    } catch (error) {
      console.error("Error generating video:", error);
      toast({
        title: "Generation Failed",
        description: "Failed to generate video. Please check your connection and try again.",
        variant: "destructive"
      });
      setIsGenerating(false);
      setJobStatus(null);
    }
  };
  const handleDownload = async () => {
    if (!jobStatus?.job_id) return;
    
    setIsDownloading(true);
    setDownloadResult(null);
    
    try {
      // Show immediate feedback for mobile users
      if (deviceCapabilities.isMobile) {
        toast({
          title: "Starting Download",
          description: deviceCapabilities.isIOS 
            ? "Preparing video... Please keep this page open."
            : "Downloading video with mobile optimization..."
        });
      }
      
      const downloadUrl = `${API_BASE_URL}/v1/jobs/${jobStatus.job_id}/download`;
      const filename = `social-story-${jobStatus.job_id}.mp4`;
      
      // Use enhanced download with retry logic and mobile optimization
      const result = await downloadVideoWithRetry(downloadUrl, {
        filename,
        minSize: 500_000, // 500KB minimum
        maxRetries: 3,
        retryDelay: 1200,
      });
      
      setDownloadResult(result);
      
      if (result.success) {
        const message = deviceCapabilities.isIOS 
          ? "Video ready! Use 'Share > Save Video' if it opened in a new tab."
          : "Your social story video has been downloaded successfully!";
          
        toast({
          title: "Download Complete",
          description: `${message} (${result.bytes} bytes${result.attempts > 1 ? `, ${result.attempts} attempts` : ''})`
        });

        // Reset form after successful download
        setFormData({
          situation: "",
          setting: ""
        });
        setJobStatus(null);
        setIsGenerating(false);
      } else {
        throw new Error(result.error || 'Download failed');
      }
      
    } catch (error) {
      console.error("Error downloading video:", error);
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      toast({
        title: "Download Failed",
        description: `${errorMessage}. ${deviceCapabilities.isMobile ? 'Check your connection and try again.' : 'Please try again.'}`,
        variant: "destructive"
      });
      
      setDownloadResult({
        success: false,
        error: errorMessage,
      });
    } finally {
      setIsDownloading(false);
    }
  };
  const handleRetry = () => {
    setJobStatus(null);
    setIsGenerating(false);
    setElapsedTime(0);
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
                  <p className="font-medium text-primary">Preparing your video generation</p>
                  <p className="text-sm text-muted-foreground">
                    This usually takes 2-3 minutes
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
            <div className="space-y-3">
              {/* Mobile-specific download tips */}
              {deviceCapabilities.isMobile && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <Smartphone className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div className="text-sm">
                      <p className="font-medium text-blue-800 mb-1">Mobile Download Tips:</p>
                      <ul className="text-blue-700 space-y-1">
                        {deviceCapabilities.recommendations.map((tip, index) => (
                          <li key={index} className="flex items-start gap-1">
                            <span className="w-1 h-1 bg-blue-600 rounded-full mt-2 flex-shrink-0"></span>
                            <span>{tip}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Download status indicator */}
              {downloadResult && !downloadResult.success && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <div className="text-sm">
                      <p className="font-medium text-red-800">Download Failed:</p>
                      <p className="text-red-700">{downloadResult.error}</p>
                      {downloadResult.attempts && (
                        <p className="text-red-600 text-xs mt-1">
                          Attempted {downloadResult.attempts} time{downloadResult.attempts > 1 ? 's' : ''}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <Button 
                onClick={handleDownload} 
                disabled={isDownloading}
                className="w-full bg-green-600 hover:bg-green-700 shadow-soft disabled:opacity-50"
              >
                {isDownloading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    {deviceCapabilities.isMobile ? 'Preparing Download...' : 'Downloading...'}
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    Download Your Social Story Video
                    {deviceCapabilities.isMobile && (
                      <Smartphone className="w-4 h-4 ml-2" />
                    )}
                  </>
                )}
              </Button>
            </div>
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