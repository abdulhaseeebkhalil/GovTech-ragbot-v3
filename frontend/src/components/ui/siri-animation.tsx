import React from 'react';
import Lottie from 'lottie-react';
import siriAnimationData from '../../../Siri.json';

interface SiriAnimationProps {
  className?: string;
  width?: number;
  height?: number;
}

export const SiriAnimation: React.FC<SiriAnimationProps> = ({ 
  className = '', 
  width = 120, 
  height = 120 
}) => {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <Lottie
        animationData={siriAnimationData}
        loop={true}
        autoplay={true}
        style={{ width, height }}
        className="drop-shadow-sm"
      />
    </div>
  );
};