import React from 'react';
import logoSrc from '../assets/risk2relief-logo.png';

export interface Risk2ReliefLogoProps {
  width?: number | string;
  height?: number | string;
  className?: string;
  style?: React.CSSProperties;
  alt?: string;
  showTagline?: boolean;
}

export const Risk2ReliefLogo: React.FC<Risk2ReliefLogoProps> = ({
  width,
  height = 40,
  className = '',
  style = {},
  alt = 'Risk2Relief — Smarter Climate Insurance for a Safer Tomorrow',
}) => {
  return (
    <img
      src={logoSrc}
      alt={alt}
      width={width}
      height={height}
      className={`risk2relief-logo-img ${className}`.trim()}
      style={{
        objectFit: 'contain',
        display: 'inline-block',
        verticalAlign: 'middle',
        borderRadius: '6px',
        ...style,
      }}
      loading="eager"
    />
  );
};

export default Risk2ReliefLogo;
