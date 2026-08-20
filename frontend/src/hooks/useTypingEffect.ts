import { useState, useEffect } from 'react';

interface UseTypingEffectOptions {
  text: string;
  speed?: number;
  startDelay?: number;
  onComplete?: () => void;
}

export const useTypingEffect = ({
  text,
  speed = 5, // milliseconds between each character
  startDelay = 0,
  onComplete
}: UseTypingEffectOptions) => {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!text) {
      setDisplayedText('');
      setIsComplete(true);
      return;
    }

    setDisplayedText('');
    setIsTyping(true);
    setIsComplete(false);

    const startTyping = () => {
      let currentIndex = 0;
      
      const typeNextCharacter = () => {
        if (currentIndex < text.length) {
          setDisplayedText(text.slice(0, currentIndex + 1));
          currentIndex++;
          setTimeout(typeNextCharacter, speed);
        } else {
          setIsTyping(false);
          setIsComplete(true);
          onComplete?.();
        }
      };

      typeNextCharacter();
    };

    if (startDelay > 0) {
      setTimeout(startTyping, startDelay);
    } else {
      startTyping();
    }

    return () => {
      setIsTyping(false);
    };
  }, [text, speed, startDelay, onComplete]);

  return {
    displayedText,
    isTyping,
    isComplete
  };
};