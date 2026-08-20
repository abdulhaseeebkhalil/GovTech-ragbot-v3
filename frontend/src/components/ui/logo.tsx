import { motion } from 'framer-motion';

export const EGovBotLogo = () => {
  return (
    <motion.div 
      className="flex items-center gap-3"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <motion.div 
        className="relative"
        whileHover={{ scale: 1.05 }}
        transition={{ type: "spring", stiffness: 300 }}
      >
        <img 
          src="/ChatGPT Image Sep 1, 2025, 03_05_41 PM.png" 
          alt="GovTech Logo" 
          className="w-12 h-12 object-cover"
        />
      </motion.div>
      <div className="flex flex-col">
        <motion.h1 
          className="text-2xl font-bold bg-gradient-to-r from-emerald-600 to-green-700 bg-clip-text text-transparent"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          GovTech
        </motion.h1>
        <motion.p 
          className="text-sm text-emerald-600 font-medium"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          by PMRU
        </motion.p>
      </div>
    </motion.div>
  );
};