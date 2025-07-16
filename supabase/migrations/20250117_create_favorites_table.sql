-- Create favorites table for storing user's favorite prompts/agents
CREATE TABLE IF NOT EXISTS public.favorites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    prompt_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, prompt_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_favorites_user_id ON public.favorites(user_id);
CREATE INDEX idx_favorites_prompt_id ON public.favorites(prompt_id);
CREATE INDEX idx_favorites_created_at ON public.favorites(created_at DESC);

-- Enable Row Level Security
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;

-- Create policy to allow users to see only their own favorites
CREATE POLICY "Users can view their own favorites" ON public.favorites
    FOR SELECT USING (auth.uid() = user_id);

-- Create policy to allow users to insert their own favorites
CREATE POLICY "Users can create their own favorites" ON public.favorites
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create policy to allow users to delete their own favorites
CREATE POLICY "Users can delete their own favorites" ON public.favorites
    FOR DELETE USING (auth.uid() = user_id);

-- Add a function to toggle favorite status
CREATE OR REPLACE FUNCTION public.toggle_favorite(p_prompt_id TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    v_exists BOOLEAN;
    v_user_id UUID;
BEGIN
    -- Get the current user's ID
    v_user_id := auth.uid();
    
    -- Check if user is authenticated
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'User must be authenticated';
    END IF;
    
    -- Check if favorite already exists
    SELECT EXISTS(
        SELECT 1 FROM public.favorites 
        WHERE user_id = v_user_id AND prompt_id = p_prompt_id
    ) INTO v_exists;
    
    IF v_exists THEN
        -- Remove favorite
        DELETE FROM public.favorites 
        WHERE user_id = v_user_id AND prompt_id = p_prompt_id;
        RETURN FALSE;
    ELSE
        -- Add favorite
        INSERT INTO public.favorites (user_id, prompt_id)
        VALUES (v_user_id, p_prompt_id);
        RETURN TRUE;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION public.toggle_favorite TO authenticated;