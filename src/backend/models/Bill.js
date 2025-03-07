const mongoose = require('mongoose');
const { v4: uuidv4 } = require('uuid');

// Define the Bill schema
const billSchema = new mongoose.Schema({
  _id: {
    type: String,
    default: uuidv4
  },
  billId: {
    type: String,
    required: true,
    index: true
  },
  date: {
    type: Date,
    default: Date.now
  },
  isFederal: {
    type: Boolean,
    default: false
  },
  state: {
    type: String,
    maxlength: 2,
    required: true
  },
  filePath: {
    type: [String],
    default: []
  },
  proposer: {
    type: String,
    default: ''
  },
  status: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: ''
  },
  citation: {
    type: [String],
    default: []
  },
  tags: {
    type: [String],
    default: []
  },
  summary: {
    type: [String],
    default: []
  },
  // Additional metadata
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
});

// Update the updatedAt field on save
billSchema.pre('save', function(next) {
  this.updatedAt = Date.now();
  next();
});

// Create the Bill model
const Bill = mongoose.model('Bill', billSchema);

module.exports = Bill;
