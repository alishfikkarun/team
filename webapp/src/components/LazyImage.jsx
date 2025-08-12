import React, {useState} from "react";

export default function LazyImage({src, alt}){
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  return (
    <div className="w-full h-80 bg-[#0d1117] flex items-center justify-center rounded overflow-hidden">
      {!loaded && !error && (
        <div className="w-full h-full flex items-center justify-center bg-gray-800 animate-pulse">
          <span className="text-sm text-gray-400">Loading image...</span>
        </div>
      )}
      {error && (
        <div className="w-full h-full flex items-center justify-center bg-gray-800">
          <span className="text-sm text-gray-400">Image not available</span>
        </div>
      )}
      <img
        src={src}
        alt={alt}
        className={`w-full h-full object-contain ${loaded ? "block" : "hidden"}`}
        onLoad={()=>setLoaded(true)}
        onError={()=>setError(true)}
        loading="lazy"
      />
    </div>
  );
}
