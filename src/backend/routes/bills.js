const express = require('express');
const router = express.Router();
const Bill = require('../models/Bill');

// Get all bills
router.get('/', async (req, res) => {
  try {
    const bills = await Bill.find();
    res.json(bills);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Search bills with filters
router.get('/search', async (req, res) => {
  try {
    const { state, isFederal, status, tags, startDate, endDate } = req.query;
    const query = {};
    
    if (state) query.state = state;
    if (isFederal !== undefined) query.isFederal = isFederal === 'true';
    if (status) query.status = status;
    if (tags) query.tags = { $in: tags.split(',') };
    
    if (startDate || endDate) {
      query.date = {};
      if (startDate) query.date.$gte = new Date(startDate);
      if (endDate) query.date.$lte = new Date(endDate);
    }
    
    const bills = await Bill.find(query);
    res.json(bills);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Get a specific bill by ID
router.get('/:id', async (req, res) => {
  try {
    const bill = await Bill.findById(req.params.id);
    if (!bill) {
      return res.status(404).json({ message: 'Bill not found' });
    }
    res.json(bill);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Create a new bill
router.post('/', async (req, res) => {
  const bill = new Bill(req.body);
  
  try {
    const newBill = await bill.save();
    res.status(201).json(newBill);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
});

// Update a bill
router.patch('/:id', async (req, res) => {
  try {
    const bill = await Bill.findById(req.params.id);
    
    if (!bill) {
      return res.status(404).json({ message: 'Bill not found' });
    }
    
    // Update fields
    Object.keys(req.body).forEach(key => {
      bill[key] = req.body[key];
    });
    
    const updatedBill = await bill.save();
    res.json(updatedBill);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
});

// Delete a bill
router.delete('/:id', async (req, res) => {
  try {
    const result = await Bill.findByIdAndDelete(req.params.id);
    
    if (!result) {
      return res.status(404).json({ message: 'Bill not found' });
    }
    
    res.json({ message: 'Bill deleted' });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Add a file path to a bill
router.post('/:id/files', async (req, res) => {
  try {
    const { filePath } = req.body;
    
    if (!filePath) {
      return res.status(400).json({ message: 'File path is required' });
    }
    
    const bill = await Bill.findById(req.params.id);
    
    if (!bill) {
      return res.status(404).json({ message: 'Bill not found' });
    }
    
    bill.filePath.push(filePath);
    const updatedBill = await bill.save();
    
    res.json(updatedBill);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
});

// Add a tag to a bill
router.post('/:id/tags', async (req, res) => {
  try {
    const { tag } = req.body;
    
    if (!tag) {
      return res.status(400).json({ message: 'Tag is required' });
    }
    
    const bill = await Bill.findById(req.params.id);
    
    if (!bill) {
      return res.status(404).json({ message: 'Bill not found' });
    }
    
    if (!bill.tags.includes(tag)) {
      bill.tags.push(tag);
      const updatedBill = await bill.save();
      res.json(updatedBill);
    } else {
      res.json(bill);
    }
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
});

// Remove a tag from a bill
router.delete('/:id/tags/:tag', async (req, res) => {
  try {
    const bill = await Bill.findById(req.params.id);
    
    if (!bill) {
      return res.status(404).json({ message: 'Bill not found' });
    }
    
    const tagIndex = bill.tags.indexOf(req.params.tag);
    
    if (tagIndex > -1) {
      bill.tags.splice(tagIndex, 1);
      const updatedBill = await bill.save();
      res.json(updatedBill);
    } else {
      res.json(bill);
    }
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
});

module.exports = router;
