import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Sparkles, Clock, Download, CheckCircle, AlertCircle } from "lucide-react";
import { toast } from "sonner";

interface SocialStoryData {
  situation: string;
  setting: string;
  age?: number;
  reading_level?: string;
  diagnosis_summary?: string;
  words_to_avoid?: string[];
  voice_preset?: string;
}

interface JobStatus {
  job_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  error?: string;
}

const READING_LEVELS = [
  { value: "early_reader", label: "Early Reader (K-2)" },
  { value: "developing_reader", label: "Developing Reader (3-5)" },
  { value: "intermediate_reader", label: "Intermediate Reader (6-8)" },
  { value: "advanced_reader", label: "Advanced Reader (9+)" },
];

const VOICE_PRESETS = [
  { value: "calm_childlike_female", label: "Calm Childlike Female" },
  { value: "gentle_male", label: "Gentle Male" },
  { value: "warm_female", label: "Warm Female" },
  { value: "friendly_neutral", label: "Friendly Neutral" },
];

export default function SocialStoryForm() {
  const [formData, setFormData] = useState<SocialStoryData>({
    situation: "",
    setting: "",
  });
  const [wordsToAvoidInput, setWordsToAvoidInput] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://api.example.com";

  const handleInputChange = (field: keyof SocialStoryData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleWordsToAvoidChange = (value: string) => {
    setWordsToAvoidInput(value);
    const words = value.split(",").map(word => word.trim()).filter(word => word);
    handleInputChange("words_to_avoid", words.length > 0 ? words : undefined);
  };

  const pollJobStatus = async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/jobs/${jobId}`);
      const data = await response.json();
      setJobStatus(data);

      if (data.status === "succeeded") {
        toast.success("Your social story video is ready!");
        return true;
      } else if (data.status === "failed") {
        toast.error(data.error || "Failed to generate video");
        setIsGenerating(false);
        return true;
      }
      return false;
    } catch (error) {
      console.error("Error polling job status:", error);
      toast.error("Error checking video status");
      setIsGenerating(false);
      return true;
    }
  };

  const startPolling = async (jobId: string) => {
    let attempts = 0;
    const maxAttempts = 150; // 5 minutes with 2-second intervals

    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      const isComplete = await pollJobStatus(jobId);
      if (isComplete) break;
      attempts++;
    }

    if (attempts >= maxAttempts) {
      toast.error("Video generation timed out. Please try again.");
      setIsGenerating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.situation.trim() || !formData.setting.trim()) {
      toast.error("Please fill in both situation and setting fields");
      return;
    }

    setIsGenerating(true);
    setJobStatus(null);
    setDownloadUrl(null);

    try {
      const payload = {
        ...formData,
        age: formData.age || undefined,
      };

      const response = await fetch(`${API_BASE_URL}/v1/social-story:start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Failed to start video generation");
      }

      const { job_id } = await response.json();
      toast.success("Video generation started!");
      
      setJobStatus({ job_id, status: "queued" });
      await startPolling(job_id);
    } catch (error) {
      console.error("Error starting job:", error);
      toast.error("Failed to start video generation");
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
      toast.success("Video downloaded successfully!");
      
      // Reset form after successful download
      setFormData({ situation: "", setting: "" });
      setWordsToAvoidInput("");
      setJobStatus(null);
      setIsGenerating(false);
    } catch (error) {
      console.error("Error downloading video:", error);
      toast.error("Failed to download video");
    }
  };

  const getStatusIcon = () => {
    if (!jobStatus) return null;
    
    switch (jobStatus.status) {
      case "queued":
      case "running":
        return <Clock className="w-4 h-4 animate-spin" />;
      case "succeeded":
        return <CheckCircle className="w-4 h-4" />;
      case "failed":
        return <AlertCircle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getStatusMessage = () => {
    if (!jobStatus) return null;
    
    switch (jobStatus.status) {
      case "queued":
        return "Your video is in the queue...";
      case "running":
        return "Creating your video story...";
      case "succeeded":
        return "Video ready for download!";
      case "failed":
        return `Failed: ${jobStatus.error || "Unknown error"}`;
      default:
        return null;
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-2 mb-4">
          <BookOpen className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold bg-gradient-hero bg-clip-text text-transparent">
            Social Story Creator
          </h1>
        </div>
        <p className="text-muted-foreground text-lg">
          Create personalized video social stories for your students
        </p>
      </div>

      <Card className="shadow-card">
        <CardHeader className="space-y-1">
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            Story Details
          </CardTitle>
          <CardDescription>
            Provide the context and setting for your social story
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="situation" className="flex items-center gap-1">
                  Situation <Badge variant="destructive" className="text-xs">Required</Badge>
                </Label>
                <Textarea
                  id="situation"
                  placeholder="e.g., passing gas in class and laughing to get attention"
                  value={formData.situation}
                  onChange={(e) => handleInputChange("situation", e.target.value)}
                  className="min-h-[100px] resize-none"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="setting" className="flex items-center gap-1">
                  Setting <Badge variant="destructive" className="text-xs">Required</Badge>
                </Label>
                <Textarea
                  id="setting"
                  placeholder="e.g., elementary classroom"
                  value={formData.setting}
                  onChange={(e) => handleInputChange("setting", e.target.value)}
                  className="min-h-[100px] resize-none"
                  required
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="age">Student Age</Label>
                <Input
                  id="age"
                  type="number"
                  placeholder="6"
                  value={formData.age || ""}
                  onChange={(e) => handleInputChange("age", e.target.value ? parseInt(e.target.value) : undefined)}
                  min="3"
                  max="18"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="reading_level">Reading Level</Label>
                <Select value={formData.reading_level || ""} onValueChange={(value) => handleInputChange("reading_level", value || undefined)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select reading level" />
                  </SelectTrigger>
                  <SelectContent>
                    {READING_LEVELS.map((level) => (
                      <SelectItem key={level.value} value={level.value}>
                        {level.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="diagnosis">Diagnosis Summary</Label>
              <Input
                id="diagnosis"
                placeholder="e.g., autism; prefers routine"
                value={formData.diagnosis_summary || ""}
                onChange={(e) => handleInputChange("diagnosis_summary", e.target.value || undefined)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="words_to_avoid">Words to Avoid</Label>
              <Input
                id="words_to_avoid"
                placeholder="e.g., gross, bad (separate with commas)"
                value={wordsToAvoidInput}
                onChange={(e) => handleWordsToAvoidChange(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="voice_preset">Voice Style</Label>
              <Select value={formData.voice_preset || ""} onValueChange={(value) => handleInputChange("voice_preset", value || undefined)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select voice style" />
                </SelectTrigger>
                <SelectContent>
                  {VOICE_PRESETS.map((voice) => (
                    <SelectItem key={voice.value} value={voice.value}>
                      {voice.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {jobStatus && (
              <Card className="bg-gradient-accent/10 border-accent">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon()}
                      <span className="font-medium">{getStatusMessage()}</span>
                    </div>
                    {jobStatus.status === "succeeded" && (
                      <Button onClick={handleDownload} size="sm" className="shadow-soft">
                        <Download className="w-4 h-4 mr-2" />
                        Download Video
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            <Button 
              type="submit" 
              disabled={isGenerating || !formData.situation.trim() || !formData.setting.trim()}
              className="w-full bg-gradient-hero hover:shadow-glow transition-all duration-300"
              size="lg"
            >
              {isGenerating ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Creating Video...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generate Social Story
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}