import SocialStoryForm from "@/components/SocialStoryForm";

const Index = () => {
  const handleImageMouseEnter = () => {
    document.body.style.overflow = 'hidden';
  };

  const handleImageMouseLeave = () => {
    document.body.style.overflow = 'auto';
  };
  return (
    <div className="min-h-screen">
      {/* Desktop Layout */}
      <div className="hidden lg:flex h-screen">
        {/* Left Column - Fixed Image */}
        <div 
          className="w-1/2 relative"
          onMouseEnter={handleImageMouseEnter}
          onMouseLeave={handleImageMouseLeave}
        >
          <img 
            src="/lovable-uploads/bb0883bb-7512-4e2b-802a-84e651c92073.png" 
            alt="Teacher and student with social story"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-transparent to-background/10"></div>
        </div>
        
        {/* Right Column - Scrollable Form */}
        <div className="w-1/2 overflow-y-auto bg-gradient-to-br from-background via-background to-secondary/20">
          <div className="px-8 py-12">
            <SocialStoryForm />
          </div>
        </div>
      </div>

      {/* Mobile Layout */}
      <div className="lg:hidden relative min-h-screen">
        {/* Background Image */}
        <div className="fixed inset-0 z-0">
          <img 
            src="/lovable-uploads/bb0883bb-7512-4e2b-802a-84e651c92073.png" 
            alt="Teacher and student with social story"
            className="w-full h-full object-cover object-top"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/80 to-background"></div>
        </div>
        
        {/* Scrollable Form Content */}
        <div className="relative z-10 min-h-screen bg-gradient-to-b from-transparent via-background/95 to-background pt-48">
          <div className="container mx-auto px-4 pb-12">
            <SocialStoryForm />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
