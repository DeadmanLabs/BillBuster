const mongoose = require('mongoose');

// MongoDB connection function
const connectDB = async () => {
  try {
    // The connection string uses environment variables that will be set in docker-compose
    const connectionString = process.env.MONGODB_URI || 'mongodb://mongodb:27017/billbuster';
    
    await mongoose.connect(connectionString, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
    
    console.log('MongoDB connected successfully');
    
    // Create a simple schema and model for testing
    const Schema = mongoose.Schema;
    const dataSchema = new Schema({
      name: String,
      value: String,
      createdAt: {
        type: Date,
        default: Date.now
      }
    });
    
    // Only create the model if it doesn't already exist
    mongoose.models.Data || mongoose.model('Data', dataSchema);
    
  } catch (error) {
    console.error('MongoDB connection error:', error.message);
    // Exit process with failure
    process.exit(1);
  }
};

module.exports = { connectDB };
